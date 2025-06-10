import datetime
from json import dumps

from telegram import Update
from telegram.ext import ContextTypes

from enums.ButtonAction import ButtonAction
from enums.Endpoint import Endpoint
from enums.JsonIdentifier import *
from enums.Method import Method
from enums.PayloadIdentifier import *

from service.telegram.KeyboardBuilder import KeyboardBuilder
from service.telegram.error_handlers import reply_if_error
from service.temptake.requests import make_request
from util.payload import split_payload, create_payload


def add_module_rows(
        json: list,
        identifier: PayloadIdentifier,
        name_key: JsonIdentifier,
        keyboard_builder: KeyboardBuilder
) -> KeyboardBuilder:
    for row in json:
        keyboard_builder.add_row()
        keyboard_builder.add_row_button(
            text=f"{row[name_key.value]}",
            callback_data=create_payload(identifier, row[JsonIdentifier.ID_KEY.value], row[name_key.value])
        )
    return keyboard_builder


def add_module_interactions(
    json: dict, identifier: PayloadIdentifier, keyboard_builder: KeyboardBuilder
) -> KeyboardBuilder:
    keyboard_builder.add_row()
    keyboard_builder.add_row_button(
        text="Get Day Data",
        callback_data=create_payload(identifier, json[JsonIdentifier.ID_KEY.value], ButtonAction.DAY)
    ).add_row_button(
        text="Get Select Data",
        callback_data=create_payload(identifier, json[JsonIdentifier.ID_KEY.value], ButtonAction.SELECT)
    ).add_row_button(
        text="Last Entry",
        callback_data=create_payload(identifier, json[JsonIdentifier.ID_KEY.value], ButtonAction.LAST)
    )
    return keyboard_builder


async def send_menu_for_group(
    update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: str, group_name: str, managers_list: list
):
    message = f"Managers for group {group_name}:\n"

    keyboard_builder = KeyboardBuilder()
    keyboard_builder = add_module_rows(
        json=managers_list,
        identifier=PayloadIdentifier.MANAGER_IDENTIFIER,
        name_key=JsonIdentifier.MAC_KEY,
        keyboard_builder=keyboard_builder
    ).add_row().add_row_button(
        text="Add Manager",
        callback_data=create_payload(PayloadIdentifier.GROUP_IDENTIFIER, group_id, ButtonAction.ADD)
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=keyboard_builder.build()
    )


async def send_menu_for_manager(
    update: Update, context: ContextTypes.DEFAULT_TYPE, workers_list: list, manager_response: dict
):
    message = f"Manager {manager_response[JsonIdentifier.MAC_KEY.value]} information:\n"
    message += f"ID: {manager_response[JsonIdentifier.ID_KEY.value]}\n"
    message += f"Created at: {manager_response[JsonIdentifier.CREATED_AT_KEY.value]}\n"

    keyboard_builder = KeyboardBuilder()

    keyboard_builder = add_module_rows(
        json=workers_list,
        identifier=PayloadIdentifier.WORKER_IDENTIFIER,
        name_key=JsonIdentifier.MAC_KEY,
        keyboard_builder=keyboard_builder
    )

    keyboard_builder = add_module_interactions(
        json=manager_response,
        identifier=PayloadIdentifier.MANAGER_IDENTIFIER,
        keyboard_builder=keyboard_builder
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=keyboard_builder.build()
    )


async def send_menu_for_worker(
    update: Update, context: ContextTypes.DEFAULT_TYPE, worker_response: dict
):
    message = f"Worker {worker_response[JsonIdentifier.MAC_KEY.value]} information:\n"
    message += f"ID: {worker_response[JsonIdentifier.ID_KEY.value]}\n"
    message += f"Created at: {worker_response[JsonIdentifier.CREATED_AT_KEY.value]}"

    keyboard_builder = KeyboardBuilder()
    keyboard_builder = add_module_interactions(
        json=worker_response,
        identifier=PayloadIdentifier.WORKER_IDENTIFIER,
        keyboard_builder=keyboard_builder
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=keyboard_builder.build()
    )

def get_iso(datetime_to_convert: datetime.datetime) -> str:
    return datetime_to_convert.isoformat(timespec="seconds")


async def send_data_for_period(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    identifier: PayloadIdentifier,
    module_id: str,
    start_timestamp: str = None,
    end_timestamp: str = None
):
    if start_timestamp is None:
        start_timestamp = get_iso(datetime.datetime.now() - datetime.timedelta(days=1))

    if end_timestamp is None:
        end_timestamp = get_iso(datetime.datetime.now())

    ep = Endpoint.ENTRY_WORKER if identifier == PayloadIdentifier.WORKER_IDENTIFIER else Endpoint.ENTRY_MANAGER

    entries_response = await make_request(
        method=Method.GET,
        endpoint=ep,
        update=update,
        json={
            JsonIdentifier.ID_KEY.value: int(module_id),
            JsonIdentifier.START_TIMESTAMP_KEY.value: start_timestamp,
            JsonIdentifier.END_TIMESTAMP_KEY.value: end_timestamp
        }
    )

    if await reply_if_error(entries_response, update, context):
        return

    message = f"Data for period from {start_timestamp} to {end_timestamp}:\n```json\n{dumps(entries_response.json(), indent=4)}\n```"
    message = message.replace("-", "\\-")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="MarkdownV2",
        text=message
    )


async def send_last_entry_data(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    identifier: PayloadIdentifier,
    module_id: str
):
    ep = Endpoint.ENTRY_WORKER_LAST if identifier == PayloadIdentifier.WORKER_IDENTIFIER else Endpoint.ENTRY_MANAGER_LAST

    entries_response = await make_request(
        method=Method.GET,
        endpoint=ep,
        update=update,
        json={JsonIdentifier.ID_KEY.value: int(module_id)}
    )

    if await reply_if_error(entries_response, update, context):
        return

    entries_json = entries_response.json()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="MarkdownV2",
        text=f"```\n{dumps(entries_json, indent=4)}\n```"
    )

# day command
async def send_day_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ...

# Handle button clicks for the inline keyboard
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    obj_identifier, obj_id, obj_name = split_payload(query.data)

    # Check if the callback data starts with the group identifier
    if obj_identifier == PayloadIdentifier.USER_IDENTIFIER:
        ...

    # If the callback data starts with the user identifier, handle it accordingly
    elif obj_identifier == PayloadIdentifier.GROUP_IDENTIFIER:
        if obj_name == ButtonAction.ADD:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=query.data
            )
        else:
            managers_response = await make_request(
                method=Method.GET,
                endpoint=Endpoint.GROUP_MANAGERS,
                update=update,
                json={JsonIdentifier.ID_KEY.value: obj_id}
            )

            if await reply_if_error(managers_response, update, context):
                return

            await send_menu_for_group(
                update=update,
                context=context,
                group_id=obj_id,
                group_name=obj_name,
                managers_list=managers_response.json()
            )

    # If the callback data starts with the manager identifier, handle it accordingly
    elif obj_identifier == PayloadIdentifier.MANAGER_IDENTIFIER:
        if obj_name == ButtonAction.DAY:
            await send_data_for_period(
                update=update,
                context=context,
                module_id=obj_id,
                identifier=PayloadIdentifier.MANAGER_IDENTIFIER
            )
        elif obj_name == ButtonAction.SELECT:
            # TODO: Implement select data functionality
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=query.data
            )
        elif obj_name == ButtonAction.LAST:
            await send_last_entry_data(
                update=update,
                context=context,
                module_id=obj_id,
                identifier=PayloadIdentifier.MANAGER_IDENTIFIER
            )
        else:
            manager_response = await make_request(
                method=Method.GET,
                endpoint=Endpoint.MANAGER,
                update=update,
                json={JsonIdentifier.ID_KEY.value: obj_id}
            )

            workers_response = await make_request(
                method=Method.GET,
                endpoint=Endpoint.MANAGER_WORKERS,
                update=update,
                json={JsonIdentifier.ID_KEY.value: obj_id}
            )

            if await reply_if_error(workers_response, update, context):
                return

            await send_menu_for_manager(
                update=update,
                context=context,
                workers_list=workers_response.json(),
                manager_response=manager_response.json()
            )

    # If the callback data starts with the worker identifier, handle it accordingly
    elif obj_identifier == PayloadIdentifier.WORKER_IDENTIFIER:
        if obj_name == ButtonAction.DAY:
            await send_data_for_period(
                update=update,
                context=context,
                module_id=obj_id,
                identifier=PayloadIdentifier.WORKER_IDENTIFIER
            )
        elif obj_name == ButtonAction.SELECT:
            # TODO: Implement select data functionality
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=query.data
            )
        elif obj_name == ButtonAction.LAST:
            await send_last_entry_data(
                update=update,
                context=context,
                module_id=obj_id,
                identifier=PayloadIdentifier.WORKER_IDENTIFIER
            )
        else:
            worker_response = await make_request(
                method=Method.GET,
                endpoint=Endpoint.WORKER,
                update=update,
                json={JsonIdentifier.ID_KEY.value: obj_id}
            )

            if await reply_if_error(worker_response, update, context):
                return

            await send_menu_for_worker(
                update=update,
                context=context,
                worker_response=worker_response.json()
            )
