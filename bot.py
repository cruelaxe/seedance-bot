import requests
import re
import time
import logging
from user_agent import generate_user_agent
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your Bot Token
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")


def generate_video(prompt: str) -> str:
    """Generate video using veoaifree.com"""
    try:
        ua = generate_user_agent()
        h = {'user-agent': ua}

        # Step 1: Get nonce
        r = requests.post('https://veoaifree.com/veo-video-generator/', headers=h)
        match = re.search(r'"nonce":"([^"]+)"', r.text)
        if not match:
            return None, "❌ Failed to get nonce"
        non = match.group(1)

        # Step 2: Generate video
        headers2 = {
            'accept': '*/*',
            'accept-language': 'en-US',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://veoaifree.com',
            'priority': 'u=1, i',
            'referer': 'https://veoaifree.com/veo-video-generator/',
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': ua,
            'x-requested-with': 'XMLHttpRequest',
        }

        data2 = {
            'action': 'veo_video_generator',
            'nonce': non,
            'prompt': prompt,
            'totalVariations': '1',
            'aspectRatio': 'VIDEO_ASPECT_RATIO_PORTRAIT',
            'actionType': 'full-video-generate',
        }

        r2 = requests.post(
            'https://veoaifree.com/wp-admin/admin-ajax.php',
            headers=headers2,
            data=data2
        )
        match2 = re.search(r'\b(\d+)\b', r2.text)
        if not match2:
            return None, "❌ Failed to get scene ID"
        l = match2.group(1)

        # Step 3: Wait and get results
        headers3 = {
            'accept': '*/*',
            'accept-language': 'en-US',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://veoaifree.com',
            'priority': 'u=1, i',
            'referer': 'https://veoaifree.com/veo-video-generator/',
            'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': ua,
            'x-requested-with': 'XMLHttpRequest',
        }

        data3 = {
            'action': 'veo_video_generator',
            'nonce': non,
            'sceneData': l,
            'actionType': 'final-video-results',
        }

        time.sleep(60)
        r3 = requests.post(
            'https://veoaifree.com/wp-admin/admin-ajax.php',
            headers=headers3,
            data=data3
        )

        return r3.text, None

    except Exception as e:
        return None, f"❌ Error: {str(e)}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    await update.message.reply_text(
        "🎬 *Welcome to Veo AI Video Generator Bot!*\n\n"
        "Just send me a text prompt and I'll generate a video for you!\n\n"
        "Example: `A cat playing piano in a jazz club`\n\n"
        "⏳ Note: Video generation takes about 60 seconds.",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "1. Send any text prompt\n"
        "2. Wait ~60 seconds\n"
        "3. Get your video!\n\n"
        "*Commands:*\n"
        "/start - Welcome message\n"
        "/help - This message",
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages and generate video"""
    prompt = update.message.text
    user = update.message.from_user

    logger.info(f"User {user.username} ({user.id}) requested: {prompt}")

    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🎬 *Generating your video...*\n\n"
        f"📝 Prompt: `{prompt}`\n\n"
        f"⏳ Please wait ~60 seconds...",
        parse_mode='Markdown'
    )

    # Generate video
    result, error = generate_video(prompt)

    if error:
        await processing_msg.edit_text(
            f"❌ *Generation Failed*\n\n{error}",
            parse_mode='Markdown'
        )
        return

    # Try to extract video URL from result
    video_url_match = re.search(r'https?://[^\s"<>]+\.mp4', result)

    if video_url_match:
        video_url = video_url_match.group(0)
        await processing_msg.delete()
        await update.message.reply_video(
            video=video_url,
            caption=f"🎬 *Your Video is Ready!*\n\n📝 Prompt: `{prompt}`",
            parse_mode='Markdown'
        )
    else:
        # Send raw result if no video URL found
        await processing_msg.edit_text(
            f"✅ *Response Received:*\n\n`{result[:3000]}`",
            parse_mode='Markdown'
        )


def main():
    """Start the bot"""
    print("🤖 Bot is starting...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
