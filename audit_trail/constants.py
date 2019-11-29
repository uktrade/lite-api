from enum import Enum, auto


class Verb(Enum):
    ADDED_NOTE = 'added note'
    REMOVED_NOTE = 'removed note'
    ADDED_QUEUES = 'added queues'
    REMOVED_QUEUES = 'removed queues'


class AuditType(Enum):
    CASE = 'CASE'
