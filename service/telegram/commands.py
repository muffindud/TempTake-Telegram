from json import dumps

from telegram import Update
from telegram.ext import ContextTypes

from enums.Endpoint import Endpoint
from enums.JsonIdentifier import *
from enums.PayloadIdentifier import *

from service.telegram.KeyboardBuilder import KeyboardBuilder
from service.telegram.buttons import add_module_rows
from service.telegram.error_handlers import reply_if_error
from service.temptake.requests import make_request
from util.security import get_user_credentials


# Register a new user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = await make_request(
        method="POST",
        endpoint=Endpoint.USER,
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
        endpoint=Endpoint.USER_GROUPS,
        update=update,
        json=get_user_credentials(update)
    )

    if await reply_if_error(response, update, context):
        return

    manager = {
        "GroupId": response.json()[0][JsonIdentifier.ID_KEY.value],
        "ManagerMac": context.args[0].upper(),
    }

    response = await make_request(
        method="POST",
        endpoint=Endpoint.GROUP_MANAGER,
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
        endpoint=Endpoint.USER_GROUPS,
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

    keyboard_builder = KeyboardBuilder()
    keyboard_builder = add_module_rows(
        json=groups,
        identifier=PayloadIdentifier.GROUP_IDENTIFIER,
        name_key=JsonIdentifier.GROUP_NAME_KEY,
        keyboard_builder=keyboard_builder
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=keyboard_builder.build()
    )
