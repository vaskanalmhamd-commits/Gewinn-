# 🎯 Gewinn - AI-Powered Earnings Platform

A comprehensive platform for managing API keys, tracking earnings, and withdrawing cryptocurrency through intelligent task automation.

## 📋 Features

### 💳 Wallet Management
- **SQLite-based wallet** with thread-safe transactions
- **Real-time balance tracking** 
- **Transaction history** with timestamps and sources
- **Automatic earnings** from bot activities (YouTube, Filecoin, etc.)

### 🤑 Cryptocurrency Withdrawal
- **Multi-asset support**: BTC, USDT, Ethereum (ETH)
- **Mock crypto payment processor** (easily extensible to real APIs)
- **Address validation** for different blockchain networks
- **Withdrawal history** with transaction hashes
- **Balance protection** - cannot withdraw more than available

### 🔑 API Key Management
- **Secure storage** in `.env` files
- **Multiple keys per provider**
- **Masked display** of sensitive keys
- **Add/remove keys via dashboard**

### ⏱️ Task Scheduler
- **YouTube browsing automation** (simulated engagement)
- **Configurable job intervals** (default 2 hours)
- **Automatic earning rewards** for completed tasks
- **Background execution** with APScheduler

### 📊 Dashboard
- **Real-time balance display** (auto-refreshes every 5s)
- **Transaction history** with filtering
- **Key management interface**
- **Withdrawal page** with full form validation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Linux/macOS (for bash script) or Windows (run commands manually)

### Installation & Startup

**Option 1: Using run.sh (Recommended)**
```bash
chmod +x run.sh
./run.sh
```

**Option 2: Manual Setup**
```bash
cd nexus-core

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Then open your browser to:
- **Dashboard**: http://localhost:8000
- **Withdrawal**: http://localhost:8000/withdraw

---

## 📁 Project Structure

```
Gewinn/
├── run.sh                    # Main startup script
├── README.md                 # This file
├── nexus-core/
│   ├── app.py               # FastAPI application & endpoints
│   ├── wallet.py            # SQLite wallet functionality (thread-safe)
│   ├── withdraw.py          # Withdrawal processor (mock crypto API)
│   ├── scheduler.py         # APScheduler for background tasks
│   ├── youtube_browser.py   # YouTube automation (Playwright)
│   ├── requirements.txt      # Python dependencies
│   ├── nexus.db             # SQLite database (auto-created)
│   ├── config/
│   │   └── keys.env         # API keys storage (auto-created)
│   └── static/
│       ├── index.html       # Dashboard page
│       └── withdraw.html    # Withdrawal page
```

---

## 🔌 API Endpoints

### Wallet Endpoints
- `GET /api/wallet/balance` - Get current balance
- `GET /api/wallet/transactions?limit=50` - Get transaction history
- `POST /api/wallet/earnings` - Add earnings (test endpoint)
  - Body: `{"amount": float, "source": "string"}`

### Withdrawal Endpoints
- `POST /api/withdraw` - Process cryptocurrency withdrawal
  - Body: `{"amount": float, "asset": "BTC|USDT|ETH", "address": "string"}`
- `GET /api/withdraw/history?limit=20` - Withdrawal history
- `GET /api/withdraw/stats` - Withdrawal statistics

### Scheduler & Keys
- `GET /api/scheduler/status` - Scheduler status and recent runs
- `GET /api/keys` - List all stored API keys
- `POST /api/keys` - Add new API key
  - Body: `{"provider": "string", "key": "string"}`

---

## 🧪 Testing

### Add Test Earnings
```bash
curl -X POST http://localhost:8000/api/wallet/earnings \
  -H "Content-Type: application/json" \
  -d '{"amount": 50, "source": "test"}'
```

### Process Withdrawal
```bash
# ETH address must be valid format (0x + 40 hex chars)
curl -X POST http://localhost:8000/api/withdraw \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10,
    "asset": "ETH",
    "address": "0x' $(python3 -c "print('a' * 40)") '"
  }'
```

### Check Balance
```bash
curl http://localhost:8000/api/wallet/balance
```

---

## ⚙️ Configuration

### Scheduler Interval
Edit `scheduler.py` line 44:
```python
def start_scheduler(interval_hours=2):  # Change 2 to desired hours
```

### Withdrawal Limits
Edit `withdraw.py` line 101:
```python
if amount > 100:  # Change 100 to max withdrawal limit
```

### Supported Assets
Edit `withdraw.py` to add more cryptocurrencies or update address validation logic.

---

## 📊 Database Schema

### `transactions` Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    amount REAL,
    source TEXT,
    status TEXT
);
```

---

## 🔐 Security Notes

- API keys are stored in plaintext in `config/keys.env` - **not for production**
- Withdrawal addresses are masked in responses but logged in full
- Mock crypto API included - replace with real payment processor for production
- All wallet operations are thread-safe with locks

---

## 🛠️ Development

### Adding New Task Types
1. Create a new function in `scheduler.py`
2. Add it as a scheduled job in `start_scheduler()`
3. Call `wallet.add_earnings()` on success

### Adding New Blockchain Support
1. Update `withdraw.py` address validation
2. Add asset to `get_withdrawal_stats()` supported list
3. Extend payment processor mock with new asset logic

### Customizing Dashboard
Edit `static/index.html` and `static/withdraw.html` - pages auto-refresh via JavaScript polling.

---

## 📝 Logs

- `tasks.log` - Scheduler task execution logs
- `youtube_activity.log` - YouTube browser automation logs
- `withdrawals.log` - Withdrawal processing logs

---

## 🔄 Data Persistence

- **Wallet data**: Stored in `nexus.db` SQLite database
- **API keys**: Stored in `config/keys.env`
- **Withdrawal history**: In-memory (cleared on restart) + logged in `withdrawals.log`

To backup:
```bash
cp nexus-core/nexus.db nexus.db.backup
cp nexus-core/config/keys.env keys.env.backup
```

---

## 📦 Dependencies

- **FastAPI** - REST API framework
- **Uvicorn** - ASGI server
- **SQLite3** - Database (built-in)
- **APScheduler** - Task scheduling
- **Playwright** - Browser automation
- **python-dotenv** - Environment variables

Install all: `pip install -r requirements.txt`

---

## 🐛 Troubleshooting

### Port 8000 Already in Use
```bash
lsof -i :8000  # Find process
kill -9 <PID>   # Kill it
```

### Database Lock Errors
Restart the server - ensures locks are released:
```bash
pkill -f 'uvicorn app:app'
./run.sh
```

### Withdrawal Address Invalid
Check address format:
- **BTC**: Starts with 1, 3, or bc1 (26+ chars)
- **ETH/USDT**: Starts with 0x (42 chars total including prefix)

### Virtual Environment Issues
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📄 License

This project is provided as-is for educational and development purposes.

---

## 🚀 Future Enhancements

- [ ] Real Filecoin SDK integration
- [ ] Real crypto payment processor (Bitso, Stripe, etc.)
- [ ] User authentication & multi-user support
- [ ] Database migrations for schema updates
- [ ] WebSocket support for real-time updates
- [ ] Advanced analytics & earnings reports
- [ ] Mobile app support
- [ ] Email notifications
- [ ] Tax reporting features

---

## 📞 Support

For issues or questions, check the logs and ensure:
1. Python 3.8+ is installed
2. All dependencies in requirements.txt are installed
3. Port 8000 is available
4. Database file has write permissions
5. config/ directory exists and is writable

---

**Happy earning! 💰**
