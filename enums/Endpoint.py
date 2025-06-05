from enum import Enum


class Endpoint(Enum):
    USER = "/api/user"
    USER_GROUPS = "/api/user/groups"
    GROUP = "/api/group"
    GROUP_MANAGER = "/api/group/manager"
    GROUP_MANAGERS = "/api/group/managers"
    MANAGER = "/api/manager"
    MANAGER_WORKERS = "/api/manager/workers"
    WORKER = "/api/worker"
    ENTRY = "/api/entry"
    ENTRY_WORKER = "/api/entry/worker"
    ENTRY_MANAGER = "/api/entry/manager"
