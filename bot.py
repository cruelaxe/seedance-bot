import os
import asyncio
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Welcome to Veo AI Video Generator Bot!\n\n"
        "Just send me a text prompt and I'll generate a video for you!\n\n"
        "Example: `A cat playing piano in a jazz club`\n\n"
        "⏳ Note: Video generation takes about 60 seconds.",
        parse_mode="Markdown"
    )

async def generate_video(prompt: str) -> str:
    print(f"🚀 Starting video generation for: {prompt}")
    
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://veoaifree.com",
        "referer": "https://veoaifree.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # Step 1: Submit prompt
    async with httpx.AsyncClient(timeout=60) as client:
        print("📤 Step 1: Submitting prompt...")
        resp1 = await client.post(
            "https://veoaifree.com/api/generate",
            json={"prompt": prompt},
            headers=headers
        )
        print(f"📥 Step 1 response: {resp1.status_code} - {resp1.text[:500]}")
        
        if resp1.status_code != 200:
            return f"❌ API Error: {resp1.status_code} - {resp1.text[:200]}"
        
        data1 = resp1.json()
        print(f"📦 Step 1 JSON: {data1}")
        
        # Get task ID
        task_id = data1.get("task_id") or data1.get("id") or data1.get("taskId")
        if not task_id:
            return f"❌ No task ID found. Response: {data1}"
        
        print(f"✅ Got task_id: {task_id}")
        
        # Step 2: Poll for result
        for i in range(30):  # Try for 5 minutes
            await asyncio.sleep(10)
            print(f"🔄 Polling attempt {i+1}...")
            
            resp2 = await client.get(
                f"https://veoaifree.com/api/status/{task_id}",
                headers=headers
            )
            print(f"📥 Poll response: {resp2.status_code} - {resp2.text[:300]}")
            
            data2 = resp2.json()
            status = data2.get("status", "")
            
            if status == "completed" or status == "done" or status == "success":
                video_url = data2.get("video_url") or data2.get("url") or data2.get("result")
                if video_url:
                    return video_url
                return f"❌ Completed but no URL: {data2}"
            
            elif status == "failed" or status == "error":
                return f"❌ Generation failed: {data2}"
        
        return "❌ Timeout: Video generation took too long"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    user = update.message.from_user
    print(f"👤 User {user.first_name} ({user.id}) requested: {prompt}")
    
    # Send processing message
    msg = await update.message.reply_text(
        f"⏳ Generating video for:\n`{prompt}`\n\nPlease wait ~60 seconds...",
        parse_mode="Markdown"
    )
    
    try:
        result = await generate_video(prompt)
        print(f"🎯 Result: {result}")
        
        if result.startswith("http"):
            await msg.edit_text(
                f"✅ Video Ready!\n\n🎬 {result}"
            )
        else:
            await msg.edit_text(result)
            
    except Exception as e:
        print(f"💥 Error: {e}")
        await msg.edit_text(f"❌ Error: {str(e)}")

def main():
    print("🤖 Bot is starting...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

