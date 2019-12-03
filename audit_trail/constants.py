from enum import Enum


class Verb(Enum):
    ADDED_NOTE = 'added note'
    REMOVED_NOTE = 'removed note'
    ADDED_QUEUES = 'added queues'
    REMOVED_QUEUES = 'removed queues'
    ADDED_ADVICE = 'added advice'
    REMOVED_ADVICE = 'removed advice'
    CREATED_FINAL_ADIVCE = 'created final advice'
    CLEARED_FINAL_ADVICE = 'cleared final advice'
    ADDED_ECJU = 'added ecju'
    ADDED_FLAGS = 'added flags'
    REMOVED_FLAGS = 'removed flags'
    UPLOADED_DOCUMENT = 'uploaded document'

