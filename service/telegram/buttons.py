from telegram import Update
from telegram.ext import ContextTypes

from param.json_params import *
from param.payload_params import *
from service.telegram.KeyboardBuilder import KeyboardBuilder

from service.telegram.error_handlers import reply_if_error
from service.temptake.requests import make_request
from util.payload_decode import split_payload


def add_module_rows(json: list, identifier: str, name_key: str, keyboard_builder: KeyboardBuilder) -> KeyboardBuilder:
    for row in json:
        keyboard_builder.add_row()
        keyboard_builder.add_row_button(
            text=f"{row[name_key]}",
            callback_data=f"{identifier}{IDENTIFIER_DELIMITER}{row[ID_KEY]}{IDENTIFIER_DELIMITER}{row[name_key]}"
        )
    return keyboard_builder


def add_module_interactions(
    json: dict, identifier: str, keyboard_builder: KeyboardBuilder
) -> KeyboardBuilder:
    keyboard_builder.add_row()
    keyboard_builder.add_row_button(
        text="Get Day Data",
        callback_data=f"{identifier}{IDENTIFIER_DELIMITER}{json[ID_KEY]}{IDENTIFIER_DELIMITER}day"
    ).add_row_button(
        text="Get Select Data",
        callback_data=f"{identifier}{IDENTIFIER_DELIMITER}{json[ID_KEY]}{IDENTIFIER_DELIMITER}select"
    )
    return keyboard_builder


# Handle button clicks for the inline keyboard
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, obj_id, obj_name = split_payload(query.data)

    # Check if the callback data starts with the group identifier
    if query.data.startswith(USER_IDENTIFIER):
        ...

    # If the callback data starts with the user identifier, handle it accordingly
    elif query.data.startswith(GROUP_IDENTIFIER):
        if obj_name == "add":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=query.data
            )
        else:
            managers_response = await make_request(
                method="GET",
                endpoint="/api/group/managers",
                update=update,
                json={ID_KEY: obj_id}
            )

            if await reply_if_error(managers_response, update, context):
                return

            message = f"Managers for group {obj_name}:\n"

            keyboard_builder = KeyboardBuilder()
            keyboard_builder = add_module_rows(
                json=managers_response.json(),
                identifier=MANAGER_IDENTIFIER,
                name_key=MAC_KEY,
                keyboard_builder=keyboard_builder
            ).add_row().add_row_button(
                text="Add Manager",
                callback_data=f"{GROUP_IDENTIFIER}{IDENTIFIER_DELIMITER}{obj_id}{IDENTIFIER_DELIMITER}add"
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                reply_markup=keyboard_builder.build()
            )

    # If the callback data starts with the manager identifier, handle it accordingly
    elif query.data.startswith(MANAGER_IDENTIFIER):
        if obj_name == "day":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=query.data
            )
        elif obj_name == "select":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=query.data
            )
        else:
            manager_response = await make_request(
                method="GET",
                endpoint="/api/manager",
                update=update,
                json={ID_KEY: obj_id}
            )

            workers_response = await make_request(
                method="GET",
                endpoint="/api/manager/workers",
                update=update,
                json={ID_KEY: obj_id}
            )

            if await reply_if_error(workers_response, update, context):
                return

            message = f"Manager {obj_name} information:\n"
            message += f"ID: {manager_response.json()[ID_KEY]}\n"
            message += f"Created at: {manager_response.json()[CREATED_AT_KEY]}\n"

            keyboard_builder = KeyboardBuilder()

            keyboard_builder = add_module_rows(
                json=workers_response.json(),
                identifier=WORKER_IDENTIFIER,
                name_key=MAC_KEY,
                keyboard_builder=keyboard_builder
            )

            keyboard_builder = add_module_interactions(
                json=manager_response.json(),
                identifier=MANAGER_IDENTIFIER,
                keyboard_builder=keyboard_builder
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                reply_markup=keyboard_builder.build()
            )

    # If the callback data starts with the worker identifier, handle it accordingly
    elif query.data.startswith(WORKER_IDENTIFIER):
        if obj_name == "day":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=query.data
            )
        elif obj_name == "select":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=query.data
            )
        else:
            worker_response = await make_request(
                method="GET",
                endpoint="/api/worker",
                update=update,
                json={ID_KEY: obj_id}
            )

            if await reply_if_error(worker_response, update, context):
                return

            worker_info = worker_response.json()
            message = f"Worker {obj_name} information:\n"
            message += f"ID: {worker_info[ID_KEY]}\n"
            message += f"Created at: {worker_info[CREATED_AT_KEY]}"

            keyboard_builder = KeyboardBuilder()
            keyboard_builder = add_module_interactions(
                json=worker_info,
                identifier=WORKER_IDENTIFIER,
                keyboard_builder=keyboard_builder
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                reply_markup=keyboard_builder.build()
            )
