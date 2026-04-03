from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import scheduler
import wallet
import withdraw

app = FastAPI()

# Start the scheduler on app startup
scheduler.start_scheduler()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

class KeyRequest(BaseModel):
    provider: str
    key: str

class EarningsRequest(BaseModel):
    amount: float
    source: str

class WithdrawalRequest(BaseModel):
    amount: float
    asset: str
    address: str

def mask_key(key):
    if len(key) <= 4:
        return key
    return key[:2] + '*' * (len(key) - 4) + key[-2:]

@app.get("/api/keys")
def get_keys():
    load_dotenv('config/keys.env')
    keys = []
    for k, v in os.environ.items():
        if k.endswith('_APIKEY'):
            provider = k.replace('_APIKEY', '')
            key_list = v.split(',')
            masked = [mask_key(key) for key in key_list]
            keys.append({"provider": provider, "keys": masked})
    return keys

@app.post("/api/keys")
def add_key(req: KeyRequest):
    provider = req.provider.upper()
    key = req.key
    env_file = 'config/keys.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f'{provider}_APIKEY='):
            current = line.strip().split('=', 1)[1]
            new = current + ',' + key
            lines[i] = f'{provider}_APIKEY={new}\n'
            found = True
            break
    if not found:
        lines.append(f'{provider}_APIKEY={key}\n')
    with open(env_file, 'w') as f:
        f.writelines(lines)
    return {"message": "Key added"}

@app.get("/api/scheduler/status")
def get_scheduler_status():
    return scheduler.get_status()

@app.get("/api/wallet/balance")
def get_wallet_balance():
    return {"balance": wallet.get_balance()}

@app.get("/api/wallet/transactions")
def get_wallet_transactions(limit: int = 50):
    return {"transactions": wallet.get_transactions(limit)}

@app.post("/api/wallet/earnings")
def add_wallet_earnings(req: EarningsRequest):
    balance = wallet.add_earnings(req.amount, req.source)
    return {"message": "Earnings added", "new_balance": balance}

@app.post("/api/withdraw")
def process_withdrawal(req: WithdrawalRequest):
    result = withdraw.process_withdrawal(req.amount, req.asset, req.address)
    return result

@app.get("/api/withdraw/history")
def get_withdrawal_history(limit: int = 20):
    return {"withdrawals": withdraw.get_withdrawal_history(limit)}

@app.get("/api/withdraw/stats")
def get_withdrawal_stats():
    return withdraw.get_withdrawal_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)