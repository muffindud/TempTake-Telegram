from datetime import timedelta, datetime, timezone
from os import environ
from json import dumps

from httpx import AsyncClient
from jwt import encode

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


SERVER_URI = f"{environ.get("SERVER_HOST")}:{environ.get("SERVER_PORT")}"
INTERNAL_SECRET = environ.get("INTERNAL_SECRET")
TOKEN_EXPIRATION = timedelta(minutes=1)


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
            }
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="MarkdownV2",
        text=f"""
```json
{dumps(response.json(), indent=4)}
```
        """
    )


async def add_manager(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_credentials = {
        "TelegramId": str(update.effective_chat.id),
        "TelegramUsername": update.effective_chat.username,
    }

    async with AsyncClient() as client:
        response = await client.request(
            method="GET",
            url=f"http://{SERVER_URI}/api/user/group",
            json=user_credentials,
            headers={
                "Authorization": f"Bearer {generate_jwt(user_credentials)}",
                "Content-Type": "application/json",
            }
        )

    manager = {
        "GroupId": response.json()[0]["id"],
        "ManagerMac": context.args[0].upper(),
    }

    async with AsyncClient() as client:
        response = await client.request(
            method="POST",
            url=f"http://{SERVER_URI}/api/group/manager/add",
            json=manager,
            headers={
                "Authorization": f"Bearer {generate_jwt(user_credentials)}",
                "Content-Type": "application/json",
            }
        )

    if response.status_code == 200:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Manager added successfully."
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Failed to add manager {response.status_code}.\n{response.text}"
        )


async def get_user_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_credentials = {
        "TelegramId": str(update.effective_chat.id),
        "TelegramUsername": update.effective_chat.username,
    }

    # Get the groups the user belongs to
    async with AsyncClient() as client:
        response = await client.request(
            method="GET",
            url=f"http://{SERVER_URI}/api/user/groups",
            json=user_credentials,
            headers={
                "Authorization": f"Bearer {generate_jwt(user_credentials)}",
                "Content-Type": "application/json",
            }
        )

    if response.status_code == 200:
        groups = response.json()
        if not groups:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You are not a member of any groups."
            )
            return

        message = "You are a member of the following groups:\n"
        for group in groups:
            message += f"- {group['name']} (ID: {group['id']})\n"

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message
        )


app = ApplicationBuilder().token(environ.get("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("manager", add_manager))
app.add_handler(CommandHandler("groups", get_user_groups))

if __name__ == "__main__":
    app.run_polling()
