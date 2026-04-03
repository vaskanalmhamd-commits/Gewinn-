from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import os
import json
import logging
import asyncio
from dotenv import load_dotenv
import task_scheduler
from database import db_manager
from security import security_manager
from task_queue import queue_manager
from condition_guard import condition_guard
import withdraw
import depin_manager
import key_manager
import metrics
import secrets
import ai_agent

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FastAPI')

app = FastAPI()
security = HTTPBasic()

# Auth config
AUTH_USER = os.getenv("GEWINN_USER", "admin")
AUTH_PASS = os.getenv("GEWINN_PASS", "gewinn2025")

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, AUTH_USER)
    correct_password = secrets.compare_digest(credentials.password, AUTH_PASS)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/dashboard.html")

@app.get("/dashboard")
def read_dashboard(user: str = Depends(get_current_user)):
    return FileResponse("static/dashboard.html")

@app.get("/withdraw")
def read_withdraw(user: str = Depends(get_current_user)):
    return FileResponse("static/withdraw.html")

# --- Security & Unlock ---
class MasterPasswordRequest(BaseModel):
    password: str

@app.post("/api/security/unlock")
async def unlock_security(req: MasterPasswordRequest, user: str = Depends(get_current_user)):
    try:
        await asyncio.to_thread(security_manager.initialize, req.password)
        # Verify with a quick test (schema initialization ensures keys table exists)
        db_manager.get_keys()
        asyncio.create_task(condition_guard.guard_loop())
        return {"message": "Sovereign environment unlocked"}
    except Exception as e:
        logger.error(f"Unlock failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Master Password")

@app.get("/api/security/status")
def get_security_status():
    return {"unlocked": security_manager._fernet is not None}

# --- Sovereign Chat Interface ---
class ChatRequest(BaseModel):
    prompt: str

@app.post("/api/agent/chat")
async def sovereign_chat(req: ChatRequest, user: str = Depends(get_current_user)):
    # The brain of the system
    result = await ai_agent.ai_agent.execute_task(req.prompt)
    return result

# --- Metrics & Stats ---
@app.get("/api/metrics")
def get_performance_metrics(user: str = Depends(get_current_user)):
    return {
        "rolling_24h_earnings": metrics.get_rolling_24h_earnings(),
        "total_earnings": metrics.get_total_earnings(),
        "system_stats": metrics.get_system_stats(),
        "depin_status": depin_manager.depin_manager.get_status(),
        "condition_status": condition_guard._status
    }

# --- Management APIs ---
@app.get("/api/keys")
def get_keys(user: str = Depends(get_current_user)):
    return key_manager.list_keys()

class KeyRequest(BaseModel):
    provider: str
    key: str
    base_url: str = None

@app.post("/api/keys")
def add_key(req: KeyRequest, user: str = Depends(get_current_user)):
    db_manager.add_key(req.provider, req.key, req.base_url)
    return {"message": "Key securely stored"}

@app.get("/api/wallet/balance")
def get_wallet_balance():
    return {"balance": db_manager.get_balance()}

class WithdrawalRequest(BaseModel):
    amount: float
    asset: str
    address: str

@app.post("/api/withdraw")
def queue_withdrawal(req: WithdrawalRequest, user: str = Depends(get_current_user)):
    return withdraw.process_withdrawal(req.amount, req.asset, req.address)

@app.get("/api/withdraw/history")
def get_withdrawal_history(limit: int = 20):
    return {"withdrawals": withdraw.get_withdrawal_history(limit)}

@app.on_event("startup")
async def startup_event():
    queue_manager.start_worker()
    task_scheduler.start_scheduler()
    logger.info("Sovereign Engine v1.0 operational.")

@app.on_event("shutdown")
def shutdown_event():
    queue_manager.stop_worker()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
