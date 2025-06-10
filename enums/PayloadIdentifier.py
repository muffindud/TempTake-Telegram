from enum import Enum

IDENTIFIER_DELIMITER = "\n"

class PayloadIdentifier(Enum):
    USER_IDENTIFIER = "u"
    GROUP_IDENTIFIER = "g"
    MANAGER_IDENTIFIER = "m"
    WORKER_IDENTIFIER = "w"
