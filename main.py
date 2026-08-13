#!/usr/bin/env python3
"""
NEURAFORGEAИ® - ORQUESTADOR CENTRAL (go.botcaza.ai)
Versión: 4.0.0 - Consolidación final
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Importar módulos del core
from core.chat_engine import responder_con_gemini
from core.affiliates_engine import affiliates_engine
from core.payment.payment_gateway import PaymentGateway

# Importar handlers del bot
from bots.monetizame_bot import (
    start, manejar_foto, manejar_ubicacion, manejar_accion,
    comando_error, ver_wallet
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("neuraforge")

# ============ CONFIGURACIÓN ============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8000))

if not TELEGRAM_TOKEN:
    logger.critical("❌ TELEGRAM_BOT_TOKEN no configurado")
    exit(1)

# ============ FASTAPI APP ============
app = FastAPI(title="NeuraforgeAI Hub", version="4.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============ TELEGRAM BOT ============
bot_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("wallet", ver_wallet))
bot_app.add_handler(CommandHandler("error", comando_error))
bot_app.add_handler(MessageHandler(filters.PHOTO, manejar_foto))
bot_app.add_handler(MessageHandler(filters.LOCATION, manejar_ubicacion))
bot_app.add_handler(CallbackQueryHandler(manejar_accion, pattern="accion_"))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_chat_gemini))

# ============ ENDPOINTS ============
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/miniapp", response_class=HTMLResponse)
async def miniapp(request: Request):
    return templates.TemplateResponse("miniapp.html", {"request": request})

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "NeuraforgeAI Hub", "version": "4.0.0"}

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    respuesta = await responder_con_gemini(data.get("user_id"), data.get("message"))
    return {"response": respuesta}

@app.get("/api/errors")
async def list_errors():
    return affiliates_engine.obtener_catalogo_errores()

# ============ INICIO ============
if __name__ == "__main__":
    import uvicorn
    # Configurar webhook en Telegram
    if WEBHOOK_URL:
        full_webhook = WEBHOOK_URL.rstrip("/") + "/webhook"
        bot_app.bot.set_webhook(full_webhook)
        logger.info(f"✅ Webhook configurado: {full_webhook}")
    
    logger.info(f"🚀 Iniciando NeuraforgeAI Hub en puerto {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
