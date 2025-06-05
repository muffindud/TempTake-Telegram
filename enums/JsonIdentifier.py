from enum import Enum


class JsonIdentifier(Enum):
    ID_KEY = "id"
    TELEGRAM_ID_KEY = "telegramId"
    TELEGRAM_USERNAME_KEY = "telegramUsername"
    GROUP_NAME_KEY = "name"
    CREATED_AT_KEY = "createdAt"
    DELETED_AT_KEY = "deletedAt"
    MAC_KEY = "mac"
