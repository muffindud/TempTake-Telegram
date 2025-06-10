from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from service.telegram.buttons import button_handler
from service.telegram.commands import *

from config import TELEGRAM_BOT_TOKEN
from enums.CommandTarget import *
from service.telegram.messages import message_handler

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler(CommandTarget.START_COMMAND.value, start))
app.add_handler(CommandHandler(CommandTarget.MANAGER_COMMAND.value, add_manager))
app.add_handler(CommandHandler(CommandTarget.GROUPS_COMMAND.value, get_user_groups))
app.add_handler(CallbackQueryHandler(button_handler, PAYLOAD_PATTERN))
app.add_handler(MessageHandler(filters.TEXT, message_handler))

if __name__ == "__main__":
    app.run_polling()
