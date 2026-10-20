import io
import json
import logging
from PIL import Image, ImageDraw
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from google import genai
from google.genai import types

TELEGRAM_TOKEN = "8663903444:AAGVZmMAJGyYQBaYed-sWDtEreRZ93NSXcA"
GEMINI_KEY = "AQ.Ab8RN6KgeHUlxQTHaHxscvo-tNV5zhxYePIJrtlQ4o7GoxAYdQ"

client = genai.Client(api_key=GEMINI_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ආයුබෝවන්! රැක් එකේ ඡායාරූපයක් එවන්න, මම miss වෙච්ච tags ලකුණු කරලා එවන්නම්.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("ඡායාරූපය පරික්ෂා කරමින් පවතී...")
    
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    image = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    img_width, img_height = image.size
    
    prompt = """
    This is a retail shelf auditing validation screen. 
    Identify the products on the shelf that DO NOT have any tag, diamond mark, or dot placed on them.
    Return ONLY a JSON array of the center coordinates [ymin, xmin, ymax, xmax] (normalized from 0 to 1000) for each missed/untagged item.
    Format: [[ymin, xmin, ymax, xmax], ...]
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        boxes = json.loads(response.text)
        draw = ImageDraw.Draw(image)
        
        for box in boxes:
            ymin, xmin, ymax, xmax = box
            cx = int(((xmin + xmax) / 2) * img_width / 1000)
            cy = int(((ymin + ymax) / 2) * img_height / 1000)
            r = 22
            
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#ff0055", outline="#ffe600", width=4)
        
        out_buffer = io.BytesIO()
        image.save(out_buffer, format="JPEG", quality=95)
        out_buffer.seek(0)
        
        await status_msg.delete()
        await update.message.reply_photo(photo=out_buffer, caption="✅ Miss වෙච්ච තැන් ලකුණු කර ඇත!")
        
    except Exception as e:
        await status_msg.edit_text(f"දෝෂයක් ඇති විය: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
