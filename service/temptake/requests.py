from typing import Any

from httpx import AsyncClient
from telegram import Update

from util.security import generate_jwt, get_user_credentials


async def make_request(
    method: str,
    url: str,
    update: Update,
    json: dict[str, Any] | None = None,
):
    async with AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            json=json,
            headers={
                "Authorization": f"Bearer {generate_jwt(get_user_credentials(update))}",
                "Content-Type": "application/json",
            }
        )
    return response
