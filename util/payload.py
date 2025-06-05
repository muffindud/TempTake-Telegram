from enums.PayloadIdentifier import *


# Split the payload into its components
def split_payload(payload: str) -> tuple[PayloadIdentifier, str, str]:
    payload_identifier, obj_id, obj_name = payload.split(IDENTIFIER_DELIMITER, 2)
    return PayloadIdentifier(payload_identifier), obj_id, obj_name


def create_payload(identifier: PayloadIdentifier, obj_id: str, obj_name: str) -> str:
    return f"{identifier.value}{IDENTIFIER_DELIMITER}{obj_id}{IDENTIFIER_DELIMITER}{obj_name}"
