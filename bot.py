import os
import requests
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ========= CONFIG =========
TELEGRAM_TOKEN = os.getenv ("7978308856:AAHAGP78WOsH2z-3i0wnAqjVm7pW9-J93v4")
GROQ_API_KEY = os.getenv("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")


MODEL_NAME = "llama-3.1-8b-instant"
MAX_HISTORY = 10  # عدد الرسائل التي يتذكرها البوت لكل مستخدم

logging.basicConfig(level=logging.INFO)

def ask_ai(messages):
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 400
        },
        timeout=30
    )

    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def generate_embarrassing_question():
    return ask_ai([
        {
            "role": "system",
            "content": "اكتب سؤالًا واحدًا فقط محرجًا اجتماعيًا أو نفسيًا بدون أي محتوى جنسي."
        }
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []

    await update.message.reply_text(
        "مرحبًا 👋\n"
        "أنا بوت ذكاء اصطناعي يتذكر سياق المحادثة 🤖\n\n"
        "• اسألني وسأتذكر ما نقوله\n"
        "• /question لسؤال محرج\n"
        "• /reset لمسح الذاكرة"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"] = []
    await update.message.reply_text("🧹 تم مسح الذاكرة. نبدأ من جديد.")

async def question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        q = generate_embarrassing_question()
        await update.message.reply_text(f"😅 {q}")
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ حدث خطأ في توليد السؤال.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_text = update.message.text

        history = context.user_data.get("history", [])

        # رسالة النظام (شخصية البوت)
        system_message = {
            "role": "system",
            "content": (
                "أنت مساعد ذكي باللغة العربية. "
                "تتذكر سياق الحديث وتبني إجاباتك عليه. "
                "كن واضحًا، محترمًا، ومفيدًا."
            )
        }

        # أضف رسالة المستخدم إلى الذاكرة
        history.append({"role": "user", "content": user_text})

        # قصّ الذاكرة إذا زادت
        history = history[-MAX_HISTORY:]

        messages = [system_message] + history

        await update.message.reply_text("🤖 أفكّر...")

        answer = ask_ai(messages)

        # أضف رد البوت إلى الذاكرة
        history.append({"role": "assistant", "content": answer})
        history = history[-MAX_HISTORY:]

        context.user_data["history"] = history

        await update.message.reply_text(answer)

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ حدث خطأ أثناء توليد الإجابة.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("question", question))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
