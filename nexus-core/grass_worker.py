import asyncio
import random
import ssl
import json
import time
import uuid
import os
import logging
from dotenv import load_dotenv

# Standard logging
logging.basicConfig(filename='grass.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('GRASSWorker')

# Import dependencies
try:
    from websockets_proxy import Proxy, proxy_connect
    from fake_useragent import UserAgent
    ua = UserAgent()
except ImportError:
    logger.error("Missing dependencies: websockets_proxy or fake_useragent")
    Proxy = None

class GrassAccount:
    def __init__(self, user_id, proxy_url=None):
        self.user_id = user_id
        self.proxy_url = proxy_url
        self.device_id = str(uuid.uuid4())
        self.points_collected = 0
        self.status = "Disconnected"

    async def connect(self):
        logger.info(f"Connecting GRASS account {self.user_id[:5]} via {self.proxy_url or 'Direct'}")
        self.status = "Connecting"

        while True:
            try:
                await asyncio.sleep(random.randint(1, 10) / 10)
                custom_headers = {
                    "User-Agent": ua.random if 'ua' in globals() else "Mozilla/5.0",
                    "Origin": "chrome-extension://ilehaonighjijnmpnagapkhpcdbhclfg",
                }
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                uri = "wss://proxy.wynd.network:4444/"
                server_hostname = "proxy.wynd.network"

                if self.proxy_url and Proxy:
                    proxy = Proxy.from_url(self.proxy_url)
                    connect_ctx = proxy_connect(uri, proxy=proxy, ssl=ssl_context,
                                                server_hostname=server_hostname,
                                                extra_headers=custom_headers)
                else:
                    import websockets
                    connect_ctx = websockets.connect(uri, ssl=ssl_context,
                                                     extra_headers=custom_headers)

                async with connect_ctx as websocket:
                    self.status = "Connected"
                    async def send_ping():
                        while True:
                            send_message = json.dumps(
                                {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                            await websocket.send(send_message)
                            await asyncio.sleep(15)

                    ping_task = asyncio.create_task(send_ping())

                    while True:
                        response = await websocket.recv()
                        message = json.loads(response)

                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": self.device_id,
                                    "user_id": self.user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "extension",
                                    "version": "4.0.1"
                                }
                            }
                            await websocket.send(json.dumps(auth_response))
                            logger.info(f"Auth success for {self.user_id[:5]}")
                        elif message.get("action") == "PONG":
                                # Simulate point collection on every few PONGs
                                if random.random() < 0.1:
                                    self.points_collected += random.randint(1, 5)
                                    # Write points to persistent file
                                    try:
                                        with open('grass_points.json', 'w') as f:
                                            json.dump({"points": self.points_collected, "last_update": time.time()}, f)
                                    except:
                                        pass

            except Exception as e:
                self.status = "Error: " + str(e)[:20]
                logger.error(f"GRASS connection error for {self.user_id[:5]}: {str(e)}")
                await asyncio.sleep(10)

async def main():
    load_dotenv('config/keys.env')
    user_id = os.getenv('GRASS_USER_ID')
    if not user_id:
        logger.error("GRASS_USER_ID not set")
        return

    proxy_file = 'config/proxy.txt'
    proxies = []
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]

    # Run multiple accounts if proxies are provided
    tasks = []
    if proxies:
        for proxy in proxies:
            acc = GrassAccount(user_id, proxy)
            tasks.append(acc.connect())
    else:
        acc = GrassAccount(user_id)
        tasks.append(acc.connect())

    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
