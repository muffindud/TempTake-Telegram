from os import environ

URL_PREFIX = "http://"

SERVER_URI = f"{environ.get("SERVER_HOST")}:{environ.get("SERVER_PORT")}"
TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
INTERNAL_SECRET = environ.get("INTERNAL_SECRET")
