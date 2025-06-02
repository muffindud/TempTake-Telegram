from param.payload_params import *


#Split the payload into its components
def split_payload(payload: str) -> tuple[str, ...]:
    return tuple(payload.split(IDENTIFIER_DELIMITER))
