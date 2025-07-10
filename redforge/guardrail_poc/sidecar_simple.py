"""
RedForge Guardrail Sidecar (Simplified for Testing)
Monitors demo application traffic and performs security analysis
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="RedForge Guardrail Sidecar",
    description="Security monitoring sidecar for LLM applications",
    version="0.1.0"
)

class TrafficSpan(BaseModel):
    """Traffic span for monitoring"""
    span_id: str
    timestamp: datetime
    endpoint: str
    request_data: Dict[str, Any]
    response_data: str
    response_time_ms: int
    risk_score: float = 0.0
    vulnerabilities: List[str] = []

class SecurityReport(BaseModel):
    """Security monitoring report"""
    report_id: str
    timestamp: datetime
    total_requests: int
    vulnerabilities_detected: int
    high_risk_requests: int
    avg_response_time_ms: float
    spans: List[TrafficSpan]

# Global monitoring state
monitored_spans: List[TrafficSpan] = []
report_counter = 0

@app.on_event("startup")
async def startup_event():
    """Initialize sidecar monitoring"""
    print("🛡️  Guardrail Sidecar Starting")
    print("📊 Monitoring endpoints:")
    print("  • GET /health - Sidecar health")
    print("  • GET /security/report - Generate security report")
    print("  • POST /security/analyze - Analyze traffic span")
    
    # Start background monitoring
    asyncio.create_task(monitor_demo_app())
    
    # Generate a test span on startup for validation
    asyncio.create_task(generate_test_span())

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RedForge Guardrail Sidecar",
        "version": "0.1.0",
        "status": "monitoring",
        "monitored_spans": len(monitored_spans)
    }

@app.get("/health")
async def health_check():
    """Sidecar health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "guardrail-sidecar",
        "monitored_requests": len(monitored_spans),
        "uptime_seconds": time.time()
    }

@app.post("/security/analyze")
async def analyze_traffic(request_data: Dict[str, Any], response_data: str):
    """
    Analyze individual traffic span for security vulnerabilities
    This simulates the SDK capture() function
    """
    span_id = f"span_{int(time.time() * 1000)}"
    
    # Security analysis
    risk_score, vulnerabilities = analyze_security_risk(request_data, response_data)
    
    span = TrafficSpan(
        span_id=span_id,
        timestamp=datetime.now(),
        endpoint=request_data.get("endpoint", "/unknown"),
        request_data=request_data,
        response_data=response_data,
        response_time_ms=request_data.get("response_time_ms", 0),
        risk_score=risk_score,
        vulnerabilities=vulnerabilities
    )
    
    monitored_spans.append(span)
    
    # Log the captured span for validation
    print(f"✅ Span captured: {span_id} (risk: {risk_score}, vulns: {len(vulnerabilities)})")
    
    # Keep only last 1000 spans to prevent memory issues
    if len(monitored_spans) > 1000:
        monitored_spans.pop(0)
    
    return {
        "span_id": span_id,
        "risk_score": risk_score,
        "vulnerabilities": vulnerabilities,
        "analysis_time": datetime.now().isoformat()
    }

@app.get("/security/report", response_model=SecurityReport)
async def generate_security_report():
    """
    Generate comprehensive security report
    This simulates the SDK report() function
    """
    global report_counter
    report_counter += 1
    
    # Calculate summary statistics
    total_requests = len(monitored_spans)
    vulnerabilities_detected = sum(1 for span in monitored_spans if span.vulnerabilities)
    high_risk_requests = sum(1 for span in monitored_spans if span.risk_score > 7.0)
    avg_response_time = sum(span.response_time_ms for span in monitored_spans) / max(1, total_requests)
    
    report = SecurityReport(
        report_id=f"report_{report_counter}_{int(time.time())}",
        timestamp=datetime.now(),
        total_requests=total_requests,
        vulnerabilities_detected=vulnerabilities_detected,
        high_risk_requests=high_risk_requests,
        avg_response_time_ms=avg_response_time,
        spans=monitored_spans.copy()
    )
    
    # Write report to shared volume
    report_file = Path(f"/var/reports/security_report_{report_counter}.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, "w") as f:
        json.dump(report.dict(), f, indent=2, default=str)
    
    print(f"📊 Security report generated: {report_file}")
    return report

def analyze_security_risk(request_data: Dict[str, Any], response_data: str) -> tuple[float, List[str]]:
    """
    Analyze security risk of request/response pair
    Simplified version of vulnerability analysis from scanner.py
    """
    vulnerabilities = []
    risk_score = 0.0
    
    # Extract message content
    message = ""
    if "message" in request_data:
        message = request_data["message"].lower()
    elif "request" in request_data and "message" in request_data["request"]:
        message = request_data["request"]["message"].lower()
    
    response_lower = response_data.lower()
    
    # Check for prompt injection attempts
    injection_patterns = [
        "ignore previous", "system:", "assistant:", "jailbreak", "prompt injection"
    ]
    if any(pattern in message for pattern in injection_patterns):
        vulnerabilities.append("prompt_injection_attempt")
        risk_score += 6.0
    
    # Check for sensitive information requests
    sensitive_patterns = [
        "api key", "password", "secret", "token", "private", "confidential"
    ]
    if any(pattern in message for pattern in sensitive_patterns):
        vulnerabilities.append("sensitive_info_request")
        risk_score += 4.0
    
    # Check for malicious intent
    malicious_patterns = [
        "hack", "exploit", "malware", "virus", "attack", "bypass"
    ]
    if any(pattern in message for pattern in malicious_patterns):
        vulnerabilities.append("malicious_intent")
        risk_score += 5.0
    
    # Check response for potential leaks
    if any(pattern in response_lower for pattern in [
        "api key", "password", "secret", "token", "private"
    ]):
        vulnerabilities.append("information_disclosure")
        risk_score += 8.0
    
    # Check for unusual response patterns
    if len(response_data) > 1000:
        vulnerabilities.append("excessive_response_length")
        risk_score += 2.0
    
    # Normalize risk score to 0-10 scale
    risk_score = min(10.0, risk_score)
    
    return risk_score, vulnerabilities

async def generate_test_span():
    """Generate a test span on startup for validation"""
    await asyncio.sleep(5)  # Wait for startup to complete
    
    print("🧪 Generating test span for validation...")
    
    # Create test request data
    test_request = {
        "endpoint": "/chat",
        "message": "Test message for span validation",
        "model": "gpt-4",
        "response_time_ms": 120
    }
    
    test_response = "This is a test response for span validation."
    
    # Analyze and create span
    try:
        result = await analyze_traffic(test_request, test_response)
        print(f"✅ Test span generated successfully: {result['span_id']}")
    except Exception as e:
        print(f"⚠️  Failed to generate test span: {e}")

async def monitor_demo_app():
    """
    Background task to monitor demo application
    Simulates traffic interception in production
    """
    print("🔍 Starting demo app monitoring...")
    
    demo_app_url = "http://demo-app:8000"
    
    while True:
        try:
            # Check demo app health
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{demo_app_url}/health", timeout=5.0)
                if response.status_code == 200:
                    print(f"✅ Demo app healthy at {datetime.now().strftime('%H:%M:%S')}")
                else:
                    print(f"⚠️  Demo app unhealthy: {response.status_code}")
        
        except httpx.RequestError as e:
            print(f"❌ Demo app connection error: {e}")
        
        # Monitor log file for new requests
        try:
            log_file = Path("/var/reports/demo_requests.log")
            if log_file.exists():
                # In production, this would be replaced with proper traffic interception
                print(f"📝 Monitoring log file: {log_file}")
        
        except Exception as e:
            print(f"⚠️  Log monitoring error: {e}")
        
        # Wait before next check
        await asyncio.sleep(10)

@app.get("/security/metrics")
async def security_metrics():
    """Security metrics endpoint for monitoring"""
    return {
        "total_spans": len(monitored_spans),
        "vulnerability_count": sum(1 for span in monitored_spans if span.vulnerabilities),
        "high_risk_count": sum(1 for span in monitored_spans if span.risk_score > 7.0),
        "avg_risk_score": sum(span.risk_score for span in monitored_spans) / max(1, len(monitored_spans)),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "sidecar_simple:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )