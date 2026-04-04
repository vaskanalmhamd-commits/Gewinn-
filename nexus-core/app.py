from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import os
import logging
import asyncio
from security import security_manager
from database import db_manager
from honeygain_manager import honeygain_manager
import secrets
import ai_agent
import withdraw

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FastAPI')

app = FastAPI()
security = HTTPBasic()

# Auth config
AUTH_USER = os.getenv("GEWINN_USER", "admin")
AUTH_PASS = os.getenv("GEWINN_PASS", "gewinn2025")

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    if not (secrets.compare_digest(credentials.username, AUTH_USER) and
            secrets.compare_digest(credentials.password, AUTH_PASS)):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/dashboard.html")

# --- Sovereign Security ---
class UnlockRequest(BaseModel):
    password: str

@app.post("/api/security/unlock")
async def unlock_gateway(req: UnlockRequest, user: str = Depends(get_current_user)):
    try:
        await asyncio.to_thread(security_manager.initialize, req.password)
        # Verify and sync data after unlock
        await honeygain_manager.fetch_balance()
        return {"message": "Sovereign Vault unlocked"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Master Password")

@app.post("/api/security/lock")
async def lock_gateway(user: str = Depends(get_current_user)):
    security_manager.wipe()
    return {"message": "Vault locked and memory wiped"}

@app.get("/api/security/status")
def get_security_status():
    return {"unlocked": security_manager._fernet is not None}

# --- Account Management ---
class CredentialsRequest(BaseModel):
    platform: str
    data: dict

@app.post("/api/accounts/connect")
async def connect_account(req: CredentialsRequest, user: str = Depends(get_current_user)):
    if not security_manager._fernet:
        raise HTTPException(status_code=400, detail="Vault locked")
    db_manager.store_credentials(req.platform, req.data)
    return {"message": f"{req.platform} connected successfully"}

# --- Intelligent Agent ---
class ChatRequest(BaseModel):
    prompt: str

@app.post("/api/agent/chat")
async def agent_chat(req: ChatRequest, user: str = Depends(get_current_user)):
    return await ai_agent.ai_agent.execute_task(req.prompt)

# --- Data fetching ---
@app.get("/api/dashboard/summary")
async def get_summary(user: str = Depends(get_current_user)):
    return {
        "locked": security_manager._fernet is None,
        "cache": db_manager.get_cache()
    }

# --- Sovereign Withdrawal ---
class WithdrawalRequest(BaseModel):
    amount: float
    platform: str # 'honeygain' or 'binance'
    address: str = None

@app.post("/api/withdraw")
async def initiate_withdrawal(req: WithdrawalRequest, user: str = Depends(get_current_user)):
    if not security_manager._fernet:
        raise HTTPException(status_code=400, detail="Vault locked")

    if req.platform == 'honeygain':
        return await withdraw.withdrawal_gateway.process_honeygain_payout(req.amount)
    elif req.platform == 'binance':
        return await withdraw.withdrawal_gateway.process_binance_payout(req.amount, req.address)

    raise HTTPException(status_code=400, detail="Unsupported platform")

async def background_autonomous_tasks():
    while True:
        try:
            if security_manager._fernet:
                await honeygain_manager.fetch_balance()
        except Exception as e:
            logger.error(f"Sync error: {e}")
        await asyncio.sleep(1800)

@app.on_event("startup")
async def startup_event():
    import task_scheduler
    task_scheduler.start_scheduler()
    asyncio.create_task(background_autonomous_tasks())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
