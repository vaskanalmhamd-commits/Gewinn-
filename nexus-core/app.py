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
from scouting_agent import scout

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

# --- Security ---
class UnlockRequest(BaseModel):
    password: str

@app.post("/api/security/unlock")
async def unlock_gateway(req: UnlockRequest, user: str = Depends(get_current_user)):
    try:
        await asyncio.to_thread(security_manager.initialize, req.password)
        return {"message": "Sovereign Vault unlocked"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Master Password")

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
    # Try fetching fresh data from Honeygain if unlocked
    if security_manager._fernet:
        await honeygain_manager.fetch_balance()

    return {
        "locked": security_manager._fernet is None,
        "cache": db_manager.get_cache()
    }

async def background_autonomous_tasks():
    """Manage periodic background tasks: scouting and threshold monitoring."""
    while True:
        try:
            # 1. Threshold Monitor
            cache = db_manager.get_cache("honeygain")
            if cache:
                usd = cache.get("balance_usd", 0)
                if usd >= 19.5:
                    logger.warning(f"⚠️ THRESHOLD ALERT: Honeygain balance is ${usd:.2f}!")

            # 2. Scouting Round (Every 12h in production, every 1h for now)
            await scout.run_scouting_round()

        except Exception as e:
            logger.error(f"Autonomous Task Error: {e}")

        await asyncio.sleep(3600) # Run cycle every hour

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_autonomous_tasks())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
