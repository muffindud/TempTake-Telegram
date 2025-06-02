from collections.abc import Sequence
from datetime import timedelta, datetime, timezone
from logging.config import IDENTIFIER
from multiprocessing.pool import worker
from os import environ
from json import dumps
from typing import Any
from unicodedata import category

from httpx import AsyncClient, Response
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


async def make_request(
    method: str,
    url: str,
    update: Update,
    json: dict[str, Any] | None = None,
):
    async with AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            json=json,
            headers={
                "Authorization": f"Bearer {generate_jwt(get_user_credentials(update))}",
                "Content-Type": "application/json",
            }
        )
    return response


async def reply_if_error(response: Response, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if response.status_code // 100 != 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Error {response.status_code}.\n{response.text}"
        )
        return True
    return False


async def send_inline_keyboard(
    response: Response,
    message: str,
    identifier: str,
    json_id_key: str,
    json_name_key: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    json = response.json()

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{item[json_name_key]}",
                callback_data=f"{identifier}{IDENTIFIER_DELIMITER}{item[json_id_key]}{IDENTIFIER_DELIMITER}{item[json_name_key]}"
            )
        ] for item in json
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


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

    if await reply_if_error(response, update, context):
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

    if await reply_if_error(response, update, context):
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Manager added successfully."
    )


# Get the groups the user is a member of
async def get_user_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = await make_request(
        method="GET",
        url=f"http://{SERVER_URI}/api/user/groups",
        update=update,
        json=get_user_credentials(update)
    )

    if await reply_if_error(response, update, context):
        return

    groups = response.json()

    if not groups:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You are not a member of any groups."
        )
        return

    message = "You are a member of the following groups:\n"
    await send_inline_keyboard(
        response=response,
        message=message,
        identifier=GROUP_IDENTIFIER,
        json_id_key=ID_KEY,
        json_name_key=GROUP_NAME_KEY,
        update=update,
        context=context
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
        _, group_id, group_name = split_payload(query.data)

        response = await make_request(
            method="GET",
            url=f"http://{SERVER_URI}/api/group/managers",
            update=update,
            json={ID_KEY: group_id}
        )

        if await reply_if_error(response, update, context):
            return

        message = f"Managers for group {group_name}:\n"
        await send_inline_keyboard(
            response=response,
            message=message,
            identifier=MANAGER_IDENTIFIER,
            json_id_key=ID_KEY,
            json_name_key=MAC_KEY,
            update=update,
            context=context
        )

    # If the callback data starts with the manager identifier, handle it accordingly
    elif query.data.startswith(MANAGER_IDENTIFIER):
        _, manager_id, manager_mac = split_payload(query.data)

        response = await make_request(
            method="GET", #
            url=f"http://{SERVER_URI}/api/manager/workers", #
            update=update,
            json={ID_KEY: manager_id} #
        )

        if await reply_if_error(response, update, context):
            return

        message = f"Workers for manager {manager_mac}:\n" #
        await send_inline_keyboard(
            response=response,
            message=message,
            identifier=WORKER_IDENTIFIER, #
            json_id_key=ID_KEY,
            json_name_key=MAC_KEY,
            update=update,
            context=context
        )

    # If the callback data starts with the worker identifier, handle it accordingly
    elif query.data.startswith(WORKER_IDENTIFIER):
        _, worker_id, worker_mac = split_payload(query.data)

        response = await make_request(
            method="GET",
            url=f"http://{SERVER_URI}/api/worker",
            update=update,
            json={ID_KEY: worker_id}
        )

        if await reply_if_error(response, update, context):
            print(response.status_code)
            print(response.text)
            print(query.data)
            return

        worker_info = response.json()
        message = f"Worker {worker_mac} information:\n"
        message += f"ID: {worker_info[ID_KEY]}\n"
        message += f"MAC: {worker_info[MAC_KEY]}\n"
        message += f"Created at: {worker_info[CREATED_AT_KEY]}"

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message
        )


app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler(START_COMMAND, start))
app.add_handler(CommandHandler(MANAGER_COMMAND, add_manager))
app.add_handler(CommandHandler(GROUPS_COMMAND, get_user_groups))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == "__main__":
    app.run_polling()
