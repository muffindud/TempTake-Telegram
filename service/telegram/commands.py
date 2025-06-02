from json import dumps

from telegram import Update
from telegram.ext import ContextTypes

from config import SERVER_URI, URL_PREFIX
from param.json_params import *
from param.payload_params import *

from service.telegram.buttons import send_inline_keyboard
from service.telegram.error_handlers import reply_if_error
from service.temptake.requests import make_request
from util.security import get_user_credentials


# Register a new user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = await make_request(
        method="POST",
        url=f"{URL_PREFIX}{SERVER_URI}/api/user",
        update=update,
        json=get_user_credentials(update)
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
    response = await make_request(
        method="GET",
        url=f"{URL_PREFIX}{SERVER_URI}/api/user/groups",
        update=update,
        json=get_user_credentials(update)
    )

    if await reply_if_error(response, update, context):
        return

    manager = {
        "GroupId": response.json()[0][ID_KEY],
        "ManagerMac": context.args[0].upper(),
    }

    response = await make_request(
        method="POST",
        url=f"{URL_PREFIX}{SERVER_URI}/api/group/manager/add",
        update=update,
        json=manager
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
        url=f"{URL_PREFIX}{SERVER_URI}/api/user/groups",
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
