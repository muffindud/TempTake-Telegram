from enums.ButtonAction import ButtonAction
from enums.PayloadIdentifier import *


# Split the payload into its components
def split_payload(payload: str) -> tuple[PayloadIdentifier, str, str]:
    payload_identifier, obj_id, obj_name = payload.split(IDENTIFIER_DELIMITER, 2)
    return PayloadIdentifier(payload_identifier), obj_id, obj_name


def create_payload(identifier: PayloadIdentifier, obj_id: str, button_action: ButtonAction | str) -> str:
    if isinstance(button_action, ButtonAction):
        button_action = button_action.value
    return f"{identifier.value}{IDENTIFIER_DELIMITER}{obj_id}{IDENTIFIER_DELIMITER}{button_action}"
