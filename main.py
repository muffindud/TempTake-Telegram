from collections.abc import Sequence
from datetime import timedelta, datetime, timezone
from logging.config import IDENTIFIER
from multiprocessing.pool import worker
from os import environ
from json import dumps
from typing import Any
from unicodedata import category

from httpx import AsyncClient
from jwt import encode

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

SERVER_URI = f"{environ.get("SERVER_HOST")}:{environ.get("SERVER_PORT")}"
TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
INTERNAL_SECRET = environ.get("INTERNAL_SECRET")
TOKEN_EXPIRATION = timedelta(minutes=1)


# Command constants
START_COMMAND = "start"
MANAGER_COMMAND = "manager"
GROUPS_COMMAND = "groups"


# Identifier constants
IDENTIFIER_DELIMITER = "\n"
USER_IDENTIFIER = "u"
GROUP_IDENTIFIER = "g"
MANAGER_IDENTIFIER = "m"
WORKER_IDENTIFIER = "w"


# JSON key constants
ID_KEY = "id"
TELEGRAM_ID_KEY = "telegramId"
TELEGRAM_USERNAME_KEY = "telegramUsername"
GROUP_NAME_KEY = "name"
CREATED_AT_KEY = "createdAt"
DELETED_AT_KEY = "deletedAt"
MAC_KEY = "mac"

# Generate a JWT token for the user
def generate_jwt(user_credentials: dict[str, str]) -> str:
    payload = {
        "TelegramId": user_credentials[TELEGRAM_ID_KEY],
        "TelegramUsername": user_credentials[TELEGRAM_USERNAME_KEY],
        "exp": datetime.now(timezone.utc) + TOKEN_EXPIRATION,
    }

    token = encode(
        payload=payload,
        key=INTERNAL_SECRET,
        algorithm="HS256"
    )

    return token


# Get user credentials from the update object
def get_user_credentials(update: Update) -> dict[str, str]:
    return {
        TELEGRAM_ID_KEY: str(update.effective_chat.id),
        TELEGRAM_USERNAME_KEY: update.effective_chat.username,
    }


#Split the payload into its components
def split_payload(payload: str) -> tuple[str, ...]:
    return tuple(payload.split(IDENTIFIER_DELIMITER))

# Register the user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with AsyncClient() as client:
        response = await client.request(
            method="POST",
            url=f"http://{SERVER_URI}/api/user",
            json=get_user_credentials(update),
            headers={
                "Authorization": f"Bearer {generate_jwt(get_user_credentials(update))}",
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


# Add a manager to the user's group
async def add_manager(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with AsyncClient() as client:
        response = await client.request(
            method="GET",
            url=f"http://{SERVER_URI}/api/user/group",
            json=get_user_credentials(update),
            headers={
                "Authorization": f"Bearer {generate_jwt(get_user_credentials(update))}",
                "Content-Type": "application/json",
            }
        )

    if response.status_code // 200:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Failed to retrieve group information {response.status_code}.\n{response.text}"
        )
        return

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
                "Authorization": f"Bearer {generate_jwt(get_user_credentials(update))}",
                "Content-Type": "application/json",
            }
        )

    if response.status_code // 100 != 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Failed to add manager {response.status_code}.\n{response.text}"
        )
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Manager added successfully."
    )


# Get the groups
async def get_user_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get the groups the user belongs to
    async with AsyncClient() as client:
        response = await client.request(
            method="GET",
            url=f"http://{SERVER_URI}/api/user/groups",
            json=get_user_credentials(update),
            headers={
                "Authorization": f"Bearer {generate_jwt(get_user_credentials(update))}",
                "Content-Type": "application/json",
            }
        )

    if response.status_code // 100 != 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Failed to retrieve groups {response.status_code}.\n{response.text}"
        )
        return

    groups = response.json()

    if not groups:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not a member of any groups."
        )
        return

    # Create an inline keyboard with the groups
    keyboard = [
        [
            InlineKeyboardButton(
                text=group[GROUP_NAME_KEY],
                callback_data=f"{GROUP_IDENTIFIER}{IDENTIFIER_DELIMITER}{group[ID_KEY]}{IDENTIFIER_DELIMITER}{group[GROUP_NAME_KEY]}",
            )
        ] for group in groups
    ]

    message = "You are a member of the following groups:\n"
    inline_keyboard = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=inline_keyboard
    )


# Handle button clicks for the inline keyboard
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Check if the callback data starts with the group identifier
    if query.data.startswith(USER_IDENTIFIER):
        ...

    # If the callback data starts with the user identifier, handle it accordingly
    elif query.data.startswith(GROUP_IDENTIFIER):
        # Extract group information from the callback data
        _, group_id, group_name = split_payload(query.data)

        # Retrieve the managers for the selected group
        async with AsyncClient() as client:
            response = await client.request(
                method="GET",
                url=f"http://{SERVER_URI}/api/group/managers",
                json={ID_KEY: group_id},
                headers={
                    "Authorization": f"Bearer {generate_jwt(get_user_credentials(update))}",
                    "Content-Type": "application/json",
                }
            )

        if response.status_code // 100 != 2:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Failed to retrieve managers for group {group_name} {response.status_code}.\n{response.text}"
            )
            return

        # Create an inline keyboard with the managers
        managers = response.json()
        keyboard = [
            [
                InlineKeyboardButton(
                    text=f"{manager[MAC_KEY]} ({manager[CREATED_AT_KEY]})",
                    callback_data=f"{MANAGER_IDENTIFIER}{IDENTIFIER_DELIMITER}{manager[ID_KEY]}{IDENTIFIER_DELIMITER}{manager[MAC_KEY]}"
                )
            ] for manager in managers
        ]

        message = f"Managers for group {group_name}:\n"
        inline_keyboard = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=inline_keyboard
        )

    # If the callback data starts with the manager identifier, handle it accordingly
    elif query.data.startswith(MANAGER_IDENTIFIER):
        # Extract manager information from the callback data
        _, manager_id, manager_mac = split_payload(query.data)

        # Retrieve the worker for the selected manager
        async with AsyncClient() as client:
            response = await client.request(
                method="GET",
                url=f"http://{SERVER_URI}/api/manager/workers",
                json={ID_KEY: manager_id},
                headers={
                    "Authorization": f"Bearer {generate_jwt(get_user_credentials(update))}",
                    "Content-Type": "application/json",
                }
            )

        if response.status_code // 100 != 2:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Failed to retrieve workers for manager {manager_mac} {response.status_code}.\n{response.text}"
            )
            return

        # Create an inline keyboard with the workers
        workers = response.json()
        keyboard = [
            [
                InlineKeyboardButton(
                    text=f"{worker[MAC_KEY]} ({worker[CREATED_AT_KEY]})",
                    callback_data=f"{WORKER_IDENTIFIER}{IDENTIFIER_DELIMITER}{worker[ID_KEY]}{IDENTIFIER_DELIMITER}{worker[MAC_KEY]}"
                )
            ] for worker in workers
        ]

        message = f"Workers for manager {manager_mac}:\n"
        inline_keyboard = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_markup=inline_keyboard
        )


    # If the callback data starts with the worker identifier, handle it accordingly
    elif query.data.startswith(WORKER_IDENTIFIER):
        ...


app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler(START_COMMAND, start))
app.add_handler(CommandHandler(MANAGER_COMMAND, add_manager))
app.add_handler(CommandHandler(GROUPS_COMMAND, get_user_groups))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == "__main__":
    app.run_polling()
