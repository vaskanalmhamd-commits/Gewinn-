import asyncio
import random
import ssl
import json
import time
import uuid
import os
import logging
from dotenv import load_dotenv

# Use standard logging to match the project
logging.basicConfig(filename='grass.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('GRASSWorker')

# Import dependencies if installed
try:
    from websockets_proxy import Proxy, proxy_connect
    from fake_useragent import UserAgent
    ua = UserAgent()
except ImportError:
    logger.error("Missing dependencies: websockets_proxy or fake_useragent")
    Proxy = None

async def connect_to_wss(user_id, proxy_url=None):
    device_id = str(uuid.uuid4())
    logger.info(f"Starting GRASS connection for device: {device_id}")

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

            if proxy_url and Proxy:
                proxy = Proxy.from_url(proxy_url)
                connect_ctx = proxy_connect(uri, proxy=proxy, ssl=ssl_context,
                                            server_hostname=server_hostname,
                                            extra_headers=custom_headers)
            else:
                import websockets
                connect_ctx = websockets.connect(uri, ssl=ssl_context,
                                                 extra_headers=custom_headers)

            async with connect_ctx as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        await websocket.send(send_message)
                        logger.debug(f"Sent PING: {send_message}")
                        await asyncio.sleep(15)

                ping_task = asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received from GRASS: {message.get('action')}")

                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "4.0.1"
                            }
                        }
                        await websocket.send(json.dumps(auth_response))
                        logger.info("Sent AUTH response")
                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        await websocket.send(json.dumps(pong_response))

        except Exception as e:
            logger.error(f"GRASS connection error: {str(e)}")
            await asyncio.sleep(5)

async def main():
    load_dotenv('config/keys.env')
    user_id = os.getenv('GRASS_USER_ID')
    if not user_id:
        logger.error("GRASS_USER_ID not set")
        return

    await connect_to_wss(user_id)

if __name__ == '__main__':
    asyncio.run(main())
