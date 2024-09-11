from collections import namedtuple
from functools import wraps

from gov_notify.service import send_email


class NotifyEmailRegistry:
    Payload = namedtuple("Payload", ["recipient_email", "payload"])

    def __init__(self):
        self._registry = []

    def register(self, *, template_id):
        def _send_email(fn):
            self._registry.append((template_id, fn.__name__))

            @wraps(fn)
            def wrapper(*args, **kwargs):
                payload = fn(*args, **kwargs)
                send_email(
                    payload.recipient_email,
                    template_id,
                    payload.payload,
                )

            return wrapper

        return _send_email


notify_email = NotifyEmailRegistry()
