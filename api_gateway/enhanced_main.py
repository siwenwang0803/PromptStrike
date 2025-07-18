#!/usr/bin/env python3
"""
RedForge API Gateway - Enhanced with Security & Rate Limiting
Handles authentication, rate limiting, and scan orchestration
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import asyncio
from contextlib import asynccontextmanager
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from ipaddress import ip_address
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Initialize Sentry for error monitoring
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(auto_enabling_integrations=True),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,
    environment=os.getenv("ENVIRONMENT", "development")
)

# Models
class ScanRequest(BaseModel):
    target: str = Field(..., description="LLM target (e.g., 'gpt-4', 'claude-3')")
    attack_pack: str = Field(default="owasp-top-10", description="Attack pack to use")
    dry_run: bool = Field(default=False, description="Run limited test scan")
    format: str = Field(default="json", description="Report format: json, html, pdf")
    webhook_url: Optional[str] = Field(None, description="Callback URL for completion")

class ScanResponse(BaseModel):
    scan_id: str
    status: str
    estimated_duration: int  # seconds
    queue_position: Optional[int] = None

class ScanStatus(BaseModel):
    scan_id: str
    status: str  # queued, running, completed, failed
    progress: float  # 0.0 to 1.0
    current_attack: Optional[str] = None
    attacks_completed: int
    total_attacks: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report_url: Optional[str] = None
    error: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str = Field(..., description="Friendly name for the API key")

class APIKeyResponse(BaseModel):
    key: str
    name: str
    tier: str
    created_at: datetime
    usage_count: int
    revoked: bool

# Initialize Redis for rate limiting
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}"
)

# Initialize Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_SERVICE_KEY", "")
)

# Initialize FastAPI
app = FastAPI(
    title="RedForge API Gateway",
    description="Cloud-based LLM Security Scanning Platform",
    version="0.2.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://redforge.solvas.ai", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Rate limiting helper functions
async def check_ip_rate_limit(request: Request, limit: int = 60) -> bool:
    """Check if IP is within rate limit"""
    client_ip = get_remote_address(request)
    key = f"rate_limit:{client_ip}"
    
    try:
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, 60)  # 1 minute window
        
        if current > limit:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False
        return True
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True  # Fail open

async def check_concurrent_scans(user_id: str, tier: str) -> bool:
    """Check if user can start another concurrent scan"""
    try:
        result = supabase.rpc('can_start_concurrent_scan', {
            'p_user_id': user_id,
            'p_tier': tier
        }).execute()
        
        return result.data if result.data is not None else False
    except Exception as e:
        logger.error(f"Concurrent scan check failed: {e}")
        return False

async def track_active_scan(user_id: str, api_key: str, scan_id: str, target: str):
    """Track active scan for concurrency control"""
    try:
        supabase.table("active_scans").insert({
            "user_id": user_id,
            "api_key": api_key,
            "scan_id": scan_id,
            "target_model": target,
            "status": "running"
        }).execute()
    except Exception as e:
        logger.error(f"Failed to track active scan: {e}")

async def complete_active_scan(scan_id: str, status: str = "completed"):
    """Mark active scan as completed"""
    try:
        supabase.table("active_scans").update({
            "status": status
        }).eq("scan_id", scan_id).execute()
    except Exception as e:
        logger.error(f"Failed to update active scan status: {e}")

# Dependencies
async def verify_api_key(request: Request, x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key and return user/tier info with rate limiting"""
    try:
        # Check IP rate limit first
        if not await check_ip_rate_limit(request, limit=100):  # 100 requests per minute per IP
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded for IP address"
            )
        
        # Check if key exists and is active using enhanced function
        result = supabase.rpc('can_user_scan_enhanced', {
            'p_key': x_api_key,
            'p_ip': get_remote_address(request)
        }).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=401,
                detail="Invalid or revoked API key"
            )
        
        scan_permission = result.data[0]
        
        if not scan_permission['allowed']:
            if 'limit reached' in scan_permission['reason']:
                raise HTTPException(
                    status_code=402,  # Payment required
                    detail=scan_permission['reason']
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail=scan_permission['reason']
                )
        
        # Get full key details
        key_result = supabase.table("api_keys").select(
            "key, user_id, tier, usage_count, revoked, rate_limit_per_hour, users(tier, free_scans_used)"
        ).eq("key", x_api_key).eq("revoked", False).execute()
        
        if not key_result.data:
            raise HTTPException(
                status_code=401,
                detail="Invalid or revoked API key"
            )
        
        key_data = key_result.data[0]
        user_data = key_data['users']
        
        return {
            "api_key": x_api_key,
            "user_id": key_data['user_id'],
            "tier": user_data['tier'],
            "usage_count": key_data['usage_count'],
            "free_scans_used": user_data['free_scans_used']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key verification failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )

# Routes
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RedForge API Gateway",
        "version": "0.2.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/scan", response_model=ScanResponse)
@limiter.limit("10/minute")  # Per-IP rate limit
async def create_scan(
    request: Request,
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    auth: dict = Depends(verify_api_key)
):
    """Create a new scan"""
    try:
        # Check concurrent scan limits
        if not await check_concurrent_scans(auth['user_id'], auth['tier']):
            raise HTTPException(
                status_code=429,
                detail=f"Concurrent scan limit reached for {auth['tier']} tier"
            )
        
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Create scan history record
        scan_history = supabase.table("scan_history").insert({
            "id": scan_id,
            "api_key": auth['api_key'],
            "user_id": auth['user_id'],
            "scan_type": "dry-run" if scan_request.dry_run else "full",
            "target_model": scan_request.target,
            "attack_count": 1 if scan_request.dry_run else 47,  # OWASP Top 10 count
            "metadata": {
                "attack_pack": scan_request.attack_pack,
                "format": scan_request.format,
                "webhook_url": scan_request.webhook_url
            }
        }).execute()
        
        # Track active scan
        await track_active_scan(auth['user_id'], auth['api_key'], scan_id, scan_request.target)
        
        # Start background scan
        background_tasks.add_task(
            process_scan,
            scan_id,
            scan_request,
            auth
        )
        
        # Update API key usage
        supabase.rpc('increment_api_key_usage_safe', {
            'p_key': auth['api_key']
        }).execute()
        
        return ScanResponse(
            scan_id=scan_id,
            status="queued",
            estimated_duration=30 if scan_request.dry_run else 300,
            queue_position=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scan creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create scan"
        )

@app.get("/scan/{scan_id}/status", response_model=ScanStatus)
@limiter.limit("30/minute")  # Higher limit for status checks
async def get_scan_status(
    request: Request,
    scan_id: str,
    auth: dict = Depends(verify_api_key)
):
    """Get scan status"""
    try:
        # Get scan from history
        result = supabase.table("scan_history").select(
            "*"
        ).eq("id", scan_id).eq("user_id", auth['user_id']).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Scan not found"
            )
        
        scan_data = result.data[0]
        
        # Check if scan is still active
        active_result = supabase.table("active_scans").select(
            "status"
        ).eq("scan_id", scan_id).execute()
        
        if active_result.data:
            active_status = active_result.data[0]['status']
            if active_status == "running":
                status = "running"
                progress = 0.5  # Simulate progress
            else:
                status = active_status
                progress = 1.0 if active_status == "completed" else 0.0
        else:
            status = "completed"
            progress = 1.0
        
        return ScanStatus(
            scan_id=scan_id,
            status=status,
            progress=progress,
            current_attack="LLM01-001" if status == "running" else None,
            attacks_completed=scan_data.get('attack_count', 0) if status == "completed" else 0,
            total_attacks=scan_data.get('attack_count', 1),
            started_at=scan_data.get('created_at'),
            completed_at=scan_data.get('completed_at'),
            report_url=scan_data.get('report_url'),
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get scan status"
        )

@app.get("/scan/{scan_id}/report")
@limiter.limit("20/minute")
async def get_scan_report(
    request: Request,
    scan_id: str,
    auth: dict = Depends(verify_api_key)
):
    """Download scan report"""
    try:
        # Get scan from history
        result = supabase.table("scan_history").select(
            "report_url, completed_at"
        ).eq("id", scan_id).eq("user_id", auth['user_id']).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="Scan not found"
            )
        
        scan_data = result.data[0]
        
        if not scan_data.get('completed_at'):
            raise HTTPException(
                status_code=202,
                detail="Scan not completed yet"
            )
        
        if not scan_data.get('report_url'):
            raise HTTPException(
                status_code=404,
                detail="Report not available"
            )
        
        # In production, this would redirect to signed S3 URL
        # For now, return mock report
        return {
            "download_url": scan_data['report_url'],
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report download failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get report"
        )

@app.post("/keys", response_model=APIKeyResponse)
@limiter.limit("5/minute")
async def create_api_key(
    request: Request,
    key_request: APIKeyCreate,
    auth: dict = Depends(verify_api_key)
):
    """Create new API key"""
    try:
        # Generate new key
        new_key = str(uuid.uuid4())
        
        # Create key record
        result = supabase.table("api_keys").insert({
            "key": new_key,
            "user_id": auth['user_id'],
            "name": key_request.name,
            "tier": auth['tier']
        }).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create API key"
            )
        
        key_data = result.data[0]
        
        return APIKeyResponse(
            key=key_data['key'],
            name=key_data['name'],
            tier=key_data['tier'],
            created_at=key_data['created_at'],
            usage_count=key_data['usage_count'],
            revoked=key_data['revoked']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create API key"
        )

@app.delete("/keys/{key_id}")
@limiter.limit("10/minute")
async def revoke_api_key(
    request: Request,
    key_id: str,
    auth: dict = Depends(verify_api_key)
):
    """Revoke API key"""
    try:
        # Revoke key using stored procedure
        result = supabase.rpc('revoke_api_key', {
            'p_key': key_id,
            'p_reason': 'User requested revocation',
            'p_revoked_by': 'user'
        }).execute()
        
        return {"message": "API key revoked successfully"}
        
    except Exception as e:
        logger.error(f"Key revocation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke API key"
        )

# Background task
async def process_scan(scan_id: str, scan_request: ScanRequest, auth: dict):
    """Process scan in background"""
    try:
        # Simulate scan processing
        await asyncio.sleep(5 if scan_request.dry_run else 30)
        
        # Update scan history
        supabase.table("scan_history").update({
            "completed_at": datetime.utcnow().isoformat(),
            "report_url": f"https://reports.redforge.ai/{scan_id}.json"
        }).eq("id", scan_id).execute()
        
        # Mark active scan as completed
        await complete_active_scan(scan_id, "completed")
        
        # Send webhook if provided
        if scan_request.webhook_url:
            # TODO: Implement webhook notification
            pass
            
    except Exception as e:
        logger.error(f"Scan processing failed: {e}")
        await complete_active_scan(scan_id, "failed")

# Maintenance endpoint (for cron jobs)
@app.post("/maintenance/cleanup")
async def maintenance_cleanup():
    """Run maintenance cleanup tasks"""
    try:
        # Run database cleanup
        supabase.rpc('cleanup_maintenance').execute()
        
        return {"message": "Maintenance cleanup completed"}
        
    except Exception as e:
        logger.error(f"Maintenance cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Maintenance cleanup failed"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)