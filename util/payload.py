from enums.ButtonAction import ButtonAction
from enums.PayloadIdentifier import *


# Split the payload into its components
def split_payload(payload: str) -> tuple[PayloadIdentifier, str, ButtonAction | str]:
    payload_identifier, obj_id, obj_name = payload.split(IDENTIFIER_DELIMITER, 2)

    try:
        button_action = ButtonAction(obj_name)
    except ValueError:
        button_action = obj_name

    return PayloadIdentifier(payload_identifier), obj_id, button_action


def create_payload(identifier: PayloadIdentifier, obj_id: str, button_action: ButtonAction | str) -> str:
    if isinstance(button_action, ButtonAction):
        button_action = button_action.value
    return f"{identifier.value}{IDENTIFIER_DELIMITER}{obj_id}{IDENTIFIER_DELIMITER}{button_action}"
