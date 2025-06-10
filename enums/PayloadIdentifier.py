from enum import Enum

IDENTIFIER_DELIMITER = "\n"
PAYLOAD_PATTERN = r"(ugmw)_(\d+)(_[a-zA-Z0-9]+)?"

class PayloadIdentifier(Enum):
    USER_IDENTIFIER = "u"
    GROUP_IDENTIFIER = "g"
    MANAGER_IDENTIFIER = "m"
    WORKER_IDENTIFIER = "w"
