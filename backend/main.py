"""
纱希 (Saki) — FastAPI Backend Entry Point

Launches the Uvicorn server with the /ws/game WebSocket endpoint
for the Vue 3 frontend to connect to.

Usage:
    python main.py                    # default: localhost:9876
    python main.py --port 9876 --host 0.0.0.0
"""
from __future__ import annotations
import argparse
import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from websocket.game_ws import GameSession

app = FastAPI(
    title="纱希 (Saki) — Yandere Horror Game Backend",
    version="2.0.0",
    docs_url=None,       # hide /docs in production
    redoc_url=None,
)

# CORS: allow the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket route ──────────────────────────────────────────────────

@app.websocket("/ws/game")
async def game_websocket(ws: WebSocket):
    await ws.accept()
    session = GameSession(ws)
    await session.run()


# ── Health check ─────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "saki-backend", "version": "2.0.0"}


# ── Root / info page ─────────────────────────────────────────────────

@app.get("/")
async def root():
    from fastapi.responses import HTMLResponse
    return HTMLResponse("""
    <html lang="zh-CN">
    <head><meta charset="utf-8"><title>纱希 Backend</title></head>
    <body style="background:#000;color:#c00;font-family:monospace;display:flex;align-items:center;justify-content:center;height:100vh;text-align:center">
    <div>
      <h1>纱希 (Saki) — Backend v2.0</h1>
      <p>WebSocket: <code>ws://localhost:9876/ws/game</code></p>
      <p>Health: <a href="/health" style="color:#c00">/health</a></p>
      <hr style="border-color:#300">
      <p style="color:#f66">这是 API 服务器，不是前端页面。</p>
      <p>请访问 <b>http://localhost:5173</b> 进入游戏。</p>
      <p style="color:#555">（确保前端已启动: cd frontend && npm run dev）</p>
    </div>
    </body>
    </html>
    """)


# ── Static file serving (production: Vue dist) ───────────────────────

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/index.html")
    async def serve_spa_fallback():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


# ── Entry point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="纱希 (Saki) Backend Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=9876, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════╗
║  纱希 (Saki) — Backend v2.0.0               ║
║  WebSocket:  ws://{args.host}:{args.port}/ws/game  ║
║  Health:     http://{args.host}:{args.port}/health  ║
╚══════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
