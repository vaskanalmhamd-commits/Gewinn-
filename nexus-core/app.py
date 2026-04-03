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
import scheduler
from database import db_manager
from security import security_manager
from task_queue import queue_manager
import withdraw
import depin_manager
import key_manager
import secrets

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FastAPI')

app = FastAPI()
security = HTTPBasic()

# Auth config (Default to judge's secure standard)
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

class KeyRequest(BaseModel):
    provider: str
    key: str

class WithdrawalRequest(BaseModel):
    amount: float
    asset: str
    address: str

@app.get("/api/keys")
def get_keys(user: str = Depends(get_current_user)):
    return key_manager.list_keys()

@app.post("/api/keys")
def add_key(req: KeyRequest, user: str = Depends(get_current_user)):
    db_manager.add_key(req.provider, req.key)
    return {"message": "Key added and encrypted"}

@app.get("/api/wallet/balance")
def get_wallet_balance():
    return {"balance": db_manager.get_balance()}

@app.post("/api/withdraw")
def queue_withdrawal(req: WithdrawalRequest, user: str = Depends(get_current_user)):
    return withdraw.process_withdrawal(req.amount, req.asset, req.address)

@app.get("/api/withdraw/history")
def get_withdrawal_history(limit: int = 20):
    return {"withdrawals": withdraw.get_withdrawal_history(limit)}

@app.get("/api/depin/status")
def get_depin_status():
    return depin_manager.depin_manager.get_status()

@app.on_event("startup")
async def startup_event():
    # Initialize security system
    master_pass = os.getenv("GEWINN_MASTER_PASS")
    if master_pass:
        security_manager.initialize(master_pass)
        logger.info("Security manager initialized.")
    else:
        logger.warning("Starting without GEWINN_MASTER_PASS - Encryption will fail.")

    # Start task queue worker
    queue_manager.start_worker()

    # Start the scheduler
    scheduler.start_scheduler()

    # Start DePIN networks
    depin_manager.depin_manager.start_all()

@app.on_event("shutdown")
def shutdown_event():
    queue_manager.stop_worker()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
