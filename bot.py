import requests
import re
import asyncio
import logging
import os
from user_agent import generate_user_agent
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")


def generate_video(prompt: str):
    """Generate video using veoaifree.com"""
    try:
        ua = generate_user_agent()
        h = {'user-agent': ua}

        # Step 1: Get nonce
        print(f"📡 Step 1: Getting nonce...")
        r = requests.post('https://veoaifree.com/veo-video-generator/', headers=h, timeout=30)
        print(f"📥 Step 1 status: {r.status_code}")
        print(f"📥 Step 1 body (first 500): {r.text[:500]}")
        
        match = re.search(r'"nonce":"([^"]+)"', r.text)
        if not match:
            print("❌ No nonce found!")
            return None, f"❌ Failed to get nonce. Response: {r.text[:200]}"
        non = match.group(1)
        print(f"✅ Nonce found: {non}")

        # Step 2: Generate video
        headers2 = {
            'accept': '*/*',
            'accept-language': 'en-US',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://veoaifree.com',
            'referer': 'https://veoaifree.com/veo-video-generator/',
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

        print(f"📡 Step 2: Sending generation request...")
        r2 = requests.post(
            'https://veoaifree.com/wp-admin/admin-ajax.php',
            headers=headers2,
            data=data2,
            timeout=30
        )
        print(f"📥 Step 2 status: {r2.status_code}")
        print(f"📥 Step 2 body: {r2.text[:500]}")

        match2 = re.search(r'\b(\d+)\b', r2.text)
        if not match2:
            return None, f"❌ Failed to get scene ID. Response: {r2.text[:300]}"
        l = match2.group(1)
        print(f"✅ Scene ID: {l}")

        # Step 3: Wait and get results
        data3 = {
            'action': 'veo_video_generator',
            'nonce': non,
            'sceneData': l,
            'actionType': 'final-video-results',
        }

        print(f"⏳ Waiting 60 seconds...")
        import time
        time.sleep(60)
        
        print(f"📡 Step 3: Getting final results...")
        r3 = requests.post(
            'https://veoaifree.com/wp-admin/admin-ajax.php',
            headers=headers2,
            data=data3,
            timeout=30
        )
        print(f"📥 Step 3 status: {r3.status_code}")
        print(f"📥 Step 3 FULL body: {r3.text}")  # Full response!

        return r3.text, None

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None, f"❌ Error: {str(e)}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Welcome to Veo AI Video Generator Bot!*\n\n"
        "Just send me a text prompt and I'll generate a video!\n\n"
        "Example: `A cat playing piano in a jazz club`\n\n"
        "⏳ Note: Video generation takes about 60 seconds.",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    prompt = update.message.text
    user = update.message.from_user
    logger.info(f"User {user.username} ({user.id}) requested: {prompt}")

    processing_msg = await update.message.reply_text(
        f"🎬 *Generating your video...*\n\n"
        f"📝 Prompt: `{prompt}`\n\n"
        f"⏳ Please wait ~60 seconds...",
        parse_mode='Markdown'
    )

    # Run blocking function in thread so bot doesn't freeze
    loop = asyncio.get_event_loop()
    result, error = await loop.run_in_executor(None, generate_video, prompt)

    if error:
        await processing_msg.edit_text(
            f"❌ *Generation Failed*\n\n{error}",
            parse_mode='Markdown'
        )
        return

    print(f"🔍 Searching for mp4 in: {result}")
    video_url_match = re.search(r'https?://[^\s"<>\\]+\.mp4', result)

    if video_url_match:
        video_url = video_url_match.group(0)
        print(f"✅ Video URL found: {video_url}")
        await processing_msg.delete()
        await update.message.reply_video(
            video=video_url,
            caption=f"🎬 *Your Video is Ready!*\n\n📝 Prompt: `{prompt}`",
            parse_mode='Markdown'
        )
    else:
        print(f"❌ No mp4 URL found in response!")
        await processing_msg.edit_text(
            f"✅ *Response Received (no video URL found):*\n\n`{result[:3000]}`",
            parse_mode='Markdown'
        )


def main():
    print("🤖 Bot is starting...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
