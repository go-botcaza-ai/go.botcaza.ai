import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from core.monetization.vision_engine import identificar_y_valorar
from core.payment.orion_caza_reversa import procesar_monetizacion
from core.payment.payment_gateway import PaymentGateway
from supabase import create_client

logger = logging.getLogger(__name__)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📸 Subir objeto para monetizar", callback_data="subir_objeto")],
        [InlineKeyboardButton("💰 Ver Billetera", callback_data="ver_wallet")],
        [InlineKeyboardButton("📊 Mis activos", callback_data="mis_activos")]
    ]
    await update.message.reply_text(
        "🤖 *NeuraforgeAI Monetízame*\n\n"
        "Te ayudo a vender, rentar o subastar cualquier objeto.\n"
        "También gestiono tu billetera digital y las comisiones.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def manejar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = str(user.id)
    photo_file = await update.message.photo[-1].get_file()
    image_bytes = await photo_file.download_as_bytearray()
    user_data[telegram_id] = {"image_bytes": bytes(image_bytes)}
    
    location_button = KeyboardButton("📍 Compartir ubicación", request_location=True)
    reply_markup = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Comparte tu ubicación para una valoración precisa.", reply_markup=reply_markup)

async def manejar_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = str(user.id)
    location = update.message.location
    lat, lon = location.latitude, location.longitude
    
    if telegram_id not in user_data or "image_bytes" not in user_data[telegram_id]:
        await update.message.reply_text("Primero envíame una foto.")
        return
    
    image_bytes = user_data[telegram_id]["image_bytes"]
    await update.message.reply_text("🔍 Analizando objeto...")
    
    try:
        resultado = await identificar_y_valorar(image_bytes, lat, lon)
        user_data[telegram_id]["resultado"] = resultado
        user_data[telegram_id]["lat"] = lat
        user_data[telegram_id]["lon"] = lon
        
        texto = (
            f"*{resultado['nombre']}*\n"
            f"💵 Precio estimado: *${resultado['precio_estimado']:.2f} MXN*\n"
            f"📊 Demanda: {resultado['demanda']}\n\n"
            "¿Qué deseas hacer?"
        )
        keyboard = [
            [InlineKeyboardButton("🛒 Vender", callback_data="accion_vender")],
            [InlineKeyboardButton("📅 Rentar", callback_data="accion_rentar")],
            [InlineKeyboardButton("🔨 Subastar", callback_data="accion_subasta")]
        ]
        await update.message.reply_text(texto, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error en valoración: {e}")
        await update.message.reply_text("⚠️ Error al procesar la imagen. Intenta con otra foto.")

async def manejar_accion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    telegram_id = str(user.id)
    
    if telegram_id not in user_data or "resultado" not in user_data[telegram_id]:
        await query.edit_message_text("Sesión expirada. Envía otra foto.")
        return
    
    resultado = user_data[telegram_id]["resultado"]
    accion = query.data
    tipo = {"accion_vender": "venta", "accion_rentar": "renta", "accion_subasta": "subasta"}.get(accion)
    if not tipo:
        await query.edit_message_text("Operación cancelada.")
        return
    
    await query.edit_message_text(f"⏳ Procesando {tipo}...")
    try:
        transaccion = await procesar_monetizacion(telegram_id, tipo, resultado['nombre'], resultado['precio_estimado'])
        supabase.table("activos_monetizados").insert({
            "telegram_id": telegram_id,
            "nombre_activo": resultado['nombre'],
            "estado": tipo,
            "precio": resultado['precio_estimado'],
            "ubicacion_lat": user_data[telegram_id].get("lat"),
            "ubicacion_lon": user_data[telegram_id].get("lon"),
            "transaccion_id": transaccion["id"]
        }).execute()
        mensaje = f"✅ *{tipo.capitalize()} activada*\nActivo: {resultado['nombre']}\nComisión: {transaccion['comision']}%"
        await query.edit_message_text(mensaje, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error en monetización: {e}")
        await query.edit_message_text("❌ Error al procesar. Contacta a soporte.")

async def ver_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        gateway = PaymentGateway()
        balance = gateway.get_balance("bitso", "mxn")
        await update.message.reply_text(
            f"💰 *Tu wallet Bitso*\nDisponible: ${balance['available']:.2f} MXN",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text("Error al consultar wallet.")

async def comando_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usa: /error <codigo> (ej. /error 404)")
        return
    consulta = " ".join(args)
    respuesta = await affiliates_engine.procesar_consulta_error(str(update.effective_user.id), consulta)
    await update.message.reply_text(respuesta, parse_mode="Markdown")

# Función para chat con Gemini (se importa en main.py)
async def manejar_chat_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    respuesta = await responder_con_gemini(str(update.effective_user.id), update.message.text)
    await update.message.reply_text(respuesta, parse_mode="Markdown")
