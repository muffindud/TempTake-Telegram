from httpx import Response
from telegram import Update
from telegram.ext import ContextTypes


async def reply_if_error(response: Response, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not response.is_success:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Error {response.status_code}.\n{response.text}"
        )
        return True
    return False
