from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from service.telegram.buttons import button_handler
from service.telegram.commands import *

from config import TELEGRAM_BOT_TOKEN
from param.command_params import *

app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler(START_COMMAND, start))
app.add_handler(CommandHandler(MANAGER_COMMAND, add_manager))
app.add_handler(CommandHandler(GROUPS_COMMAND, get_user_groups))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == "__main__":
    app.run_polling()
