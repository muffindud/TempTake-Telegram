from datetime import datetime, timezone
from jwt import encode
from telegram import Update

from enums.JsonIdentifier import *
from config import INTERNAL_SECRET, TOKEN_EXPIRATION


# Generate a JWT token for the user
def generate_jwt(user_credentials: dict[str, str]) -> str:
    payload = {
        "TelegramId": user_credentials[JsonIdentifier.TELEGRAM_ID_KEY.value],
        "TelegramUsername": user_credentials[JsonIdentifier.TELEGRAM_USERNAME_KEY.value],
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
        JsonIdentifier.TELEGRAM_ID_KEY.value: str(update.effective_chat.id),
        JsonIdentifier.TELEGRAM_USERNAME_KEY.value: update.effective_chat.username,
    }
