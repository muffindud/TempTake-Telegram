from os import environ

from httpx import AsyncClient

from json import dumps

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_credentials = {
        "TelegramId": str(update.effective_chat.id),
        "TelegramUsername": update.effective_chat.username,
    }

    async with AsyncClient() as client:
        response = await client.request(
            method="POST",
            url="http://temptake-server.duckdns.org:8080/api/user",
            json=user_credentials,
            headers={
                # "Authorization": f"Bearer {environ.get('API_KEY')}",
                "Content-Type": "application/json",
            },
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="MarkdownV2",
        text=f"""
```json
{dumps(user_credentials, indent=4)}
```
        """
    )



app = ApplicationBuilder().token(environ.get("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    app.run_polling()
