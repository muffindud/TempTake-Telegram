from telegram import Update
from telegram.ext import ContextTypes

from service.telegram.buttons import awaiting_worker_mac, awaiting_manager_mac
from service.telegram.error_handlers import reply_if_error
from service.temptake.requests import make_request
from enums.JsonIdentifier import JsonIdentifier
from enums.Endpoint import Endpoint
from enums.Method import Method


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    group_id = awaiting_manager_mac.pop(update.effective_chat.id, None)
    if group_id is not None:
        manager_mac = update.message.text.upper()
        manager = {
            JsonIdentifier.ID_KEY.value: group_id,
            JsonIdentifier.MAC_KEY.value: manager_mac,
        }

        response = await make_request(
            method=Method.POST,
            endpoint=Endpoint.GROUP_MANAGER,
            update=update,
            json=manager
        )

        if await reply_if_error(response, update, context):
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Manager {manager_mac} added successfully."
        )
        return

    manager_id = awaiting_worker_mac.pop(update.effective_chat.id, None)
    if manager_id is not None:
        worker_mac = update.message.text.upper()
        worker = {
            JsonIdentifier.ID_KEY.value: manager_id,
            JsonIdentifier.MAC_KEY.value: worker_mac,
        }

        response = await make_request(
            method=Method.POST,
            endpoint=Endpoint.WORKER,
            update=update,
            json=worker
        )

        if await reply_if_error(response, update, context):
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Worker {worker_mac} added successfully."
        )
        return
