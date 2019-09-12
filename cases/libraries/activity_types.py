class BaseActivityType:
    choices = []

    @classmethod
    def get_text(cls, choice):
        return [x for x in cls.choices if x[0] == choice][0][1]


class CaseActivityType(BaseActivityType):
    ADD_FLAGS = 'add_flags'
    REMOVE_FLAGS = 'remove_flags'
    ADD_REMOVE_FLAGS = 'add_remove_flags'
    MOVE_QUEUE = 'move_queue'

    BaseActivityType.choices.extend(
        [
            (ADD_FLAGS, 'added flags: {flags}'),
            (REMOVE_FLAGS, 'removed flags: {flags}'),
            (ADD_REMOVE_FLAGS, 'added flags: {added_flags}, and removed: {removed_flags}'),
            (MOVE_QUEUE, 'moved {case_name} to queue {queue}')
        ]
    )
