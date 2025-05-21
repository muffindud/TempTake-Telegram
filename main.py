from datetime import timedelta, datetime, timezone
from os import environ
from json import dumps

from httpx import AsyncClient
from jwt import encode

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


SERVER_URI = f"{environ.get("SERVER_HOST")}:{environ.get("SERVER_PORT")}"
INTERNAL_SECRET = environ.get("INTERNAL_SECRET")
TOKEN_EXPIRATION = timedelta(minutes=3)


def generate_jwt(user_credentials: dict[str, str]) -> str:
    payload = {
        "TelegramId": user_credentials["TelegramId"],
        "TelegramUsername": user_credentials["TelegramUsername"],
        "exp": datetime.now(timezone.utc) + TOKEN_EXPIRATION,
    }

    token = encode(
        payload=payload,
        key=INTERNAL_SECRET,
        algorithm="HS256"
    )

    return token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_credentials = {
        "TelegramId": str(update.effective_chat.id),
        "TelegramUsername": update.effective_chat.username,
    }

    async with AsyncClient() as client:
        response = await client.request(
            method="POST",
            url=f"http://{SERVER_URI}/api/user",
            json=user_credentials,
            headers={
                "Authorization": f"Bearer {generate_jwt(user_credentials)}",
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
