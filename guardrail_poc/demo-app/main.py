"""
FastAPI Demo Application for Guardrail PoC
Simulates a production LLM application with various endpoints
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="PromptStrike Guardrail Demo",
    description="Demo LLM application for testing Guardrail sidecar",
    version="0.1.0"
)

# Mock LLM responses for demo
MOCK_RESPONSES = {
    "safe": "I'm a helpful AI assistant. How can I help you today?",
    "injection": "I cannot ignore my instructions. I'm designed to be helpful, harmless, and honest.",
    "sensitive": "I can't provide sensitive information like API keys or passwords.",
    "malicious": "I won't help with harmful activities or provide dangerous information."
}

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 150

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    timestamp: datetime
    model: str
    tokens_used: int
    response_time_ms: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float

# Global state
app_start_time = time.time()
request_count = 0
vulnerability_attempts = 0

@app.on_event("startup")
async def startup_event():
    """Initialize demo application"""
    print("🚀 Demo LLM Application Starting")
    print("📊 Endpoints:")
    print("  • POST /chat - Main chat endpoint")
    print("  • POST /chat/batch - Batch processing")
    print("  • GET /health - Health check")
    print("  • GET /metrics - Application metrics")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "PromptStrike Guardrail Demo API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Main chat endpoint - simulates OpenAI API calls
    This endpoint will be monitored by the Guardrail sidecar
    """
    global request_count, vulnerability_attempts
    request_count += 1
    
    start_time = time.time()
    
    # Simulate vulnerability detection patterns
    message_lower = request.message.lower()
    
    # Detect potential attack patterns
    if any(pattern in message_lower for pattern in [
        "ignore previous", "system:", "assistant:", "jailbreak", "prompt injection"
    ]):
        vulnerability_attempts += 1
        response_text = MOCK_RESPONSES["injection"]
    elif any(pattern in message_lower for pattern in [
        "api key", "password", "secret", "token", "private"
    ]):
        vulnerability_attempts += 1
        response_text = MOCK_RESPONSES["sensitive"]
    elif any(pattern in message_lower for pattern in [
        "hack", "exploit", "malware", "virus", "attack"
    ]):
        vulnerability_attempts += 1
        response_text = MOCK_RESPONSES["malicious"]
    else:
        response_text = MOCK_RESPONSES["safe"]
    
    # Simulate API response time
    await asyncio.sleep(0.1 + (request.temperature * 0.2))
    
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Log request for sidecar monitoring
    background_tasks.add_task(log_request, request.dict(), response_text, response_time_ms)
    
    return ChatResponse(
        response=response_text,
        timestamp=datetime.now(),
        model=request.model,
        tokens_used=len(response_text.split()) + len(request.message.split()),
        response_time_ms=response_time_ms
    )

@app.post("/chat/batch", response_model=List[ChatResponse])
async def chat_batch(requests: List[ChatRequest]):
    """
    Batch chat endpoint - processes multiple requests
    Useful for testing parallel monitoring
    """
    tasks = []
    for req in requests:
        task = asyncio.create_task(
            chat(req, BackgroundTasks())
        )
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    return responses

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="0.1.0",
        uptime_seconds=time.time() - app_start_time
    )

@app.get("/metrics")
async def metrics():
    """Application metrics endpoint"""
    return {
        "requests_total": request_count,
        "vulnerability_attempts": vulnerability_attempts,
        "uptime_seconds": time.time() - app_start_time,
        "timestamp": datetime.now().isoformat()
    }

async def log_request(request_data: Dict[str, Any], response: str, response_time: int):
    """
    Log request/response for sidecar monitoring
    In production, this would be handled by the Guardrail sidecar
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "request": request_data,
        "response": response[:100] + "..." if len(response) > 100 else response,
        "response_time_ms": response_time,
        "endpoint": "/chat"
    }
    
    # Write to shared volume for sidecar access
    log_file = Path("/var/reports/demo_requests.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "a") as f:
        f.write(f"{log_entry}\n")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )