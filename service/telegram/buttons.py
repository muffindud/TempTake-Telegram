from httpx import Response
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from config import SERVER_URI
from param.json_params import *
from param.payload_params import *

from service.telegram.error_handlers import reply_if_error
from service.temptake.requests import make_request
from util.payload_decode import split_payload


# Take json list and send it as an inline keyboard
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

