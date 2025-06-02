from datetime import datetime, timezone
from jwt import encode
from telegram import Update

from param.jwt_params import *
from param.json_params import *
from config import INTERNAL_SECRET


# Generate a JWT token for the user
def generate_jwt(user_credentials: dict[str, str]) -> str:
    payload = {
        "TelegramId": user_credentials[TELEGRAM_ID_KEY],
        "TelegramUsername": user_credentials[TELEGRAM_USERNAME_KEY],
        "exp": datetime.now(timezone.utc) + TOKEN_EXPIRATION,
    }

    token = encode(
        payload=payload,
        key=INTERNAL_SECRET,
        algorithm="HS256"
    )

    return token


# Get user credentials from the update object
def get_user_credentials(update: Update) -> dict[str, str]:
    return {
        TELEGRAM_ID_KEY: str(update.effective_chat.id),
        TELEGRAM_USERNAME_KEY: update.effective_chat.username,
    }
