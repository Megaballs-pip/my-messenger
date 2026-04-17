import asyncio
import websockets
import json
import os
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

users = {}

async def handler(ws):
    username = None
    try:
        msg = await ws.recv()
        data = json.loads(msg)
        if data["type"] == "register":
            username = data["username"]
            if username in users:
                await ws.send(json.dumps({"type": "error", "text": "Имя занято"}))
                return
            users[username] = ws
            await ws.send(json.dumps({"type": "users_list", "users": list(users.keys())}))
            await broadcast({"type": "info", "text": f"✨ {username} присоединился"})
            await broadcast_users_list()
        
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "public":
                await broadcast({"type": "public", "from": username, "text": data["text"], "time": datetime.now().strftime("%H:%M")})
            elif data["type"] == "private":
                target = data["to"]
                if target in users:
                    await users[target].send(json.dumps({"type": "private", "from": username, "text": data["text"], "time": datetime.now().strftime("%H:%M")}))
            elif data["type"] == "typing":
                target = data.get("to")
                if target and target in users:
                    await users[target].send(json.dumps({"type": "typing", "from": username}))
    except:
        pass
    finally:
        if username and username in users:
            del users[username]
            await broadcast({"type": "info", "text": f"👋 {username} покинул чат"})
            await broadcast_users_list()

async def broadcast(msg):
    if users:
        await asyncio.wait([u.send(json.dumps(msg)) for u in users.values()])

async def broadcast_users_list():
    await broadcast({"type": "users_list", "users": list(users.keys())})

async def start_websocket():
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"✅ WebSocket сервер на порту {port}")
        await asyncio.Future()

def start_http():
    port = int(os.environ.get("PORT", 8000))
    with HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler) as httpd:
        print(f"✅ HTTP сервер на порту {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Запускаем HTTP сервер в отдельном потоке
    threading.Thread(target=start_http, daemon=True).start()
    # Запускаем WebSocket сервер
    asyncio.run(start_websocket())
