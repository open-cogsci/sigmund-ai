import logging
from . import config
logger = logging.getLogger('sigmund')


class LimitsChecker:
    """Centralized checks for all usage limits (hourly, hard, soft, and
    suspension).

    This class encapsulates the limit logic that was previously scattered
    throughout sigmund.py. It provides a single :meth:`blocked_message`
    method that returns the first applicable limit-exceeded message, or
    ``None`` if the user is allowed to send messages.
    """

    def __init__(self, sigmund):
        self._sigmund = sigmund
        self._db = sigmund.database

    # -- Individual limit checks -------------------------------------------

    def hourly_exceeded(self) -> bool:
        """Returns True if the hourly token limit has been exceeded."""
        return self._db.get_activity(
            time_delta={'hours': 1}
        ) > config.hourly_token_limit

    def hard_exceeded(self) -> bool:
        """Returns True if the hard (weekly) token limit has been exceeded."""
        return self._db.get_activity(
            time_delta={'days': config.soft_token_range}
        ) > config.hard_token_limit

    def soft_exceeded(self) -> bool:
        """Returns True if the soft (weekly) token limit has been exceeded
        AND the user has no activity buffer remaining.

        When the soft limit is exceeded but a buffer is available, the user
        is allowed to continue (drawing from the buffer), so this returns
        False.
        """
        weekly_activity = self._db.get_activity(
            time_delta={'days': config.soft_token_range}
        )
        if weekly_activity < config.soft_token_limit:
            return False
        return self._db.get_activity_buffer() <= 0

    def suspended(self) -> bool:
        """Returns True if the user's account is suspended."""
        return self._db.get_suspended()

    # -- Aggregated checks -------------------------------------------------

    def blocked_message(self) -> str | None:
        """Returns the first applicable limit-exceeded message, or ``None`` if
        the user is allowed to send messages.

        The order of checks matters: hard and hourly limits take precedence
        over the soft limit, and suspension takes the highest precedence.
        """
        if self.suspended():
            return config.suspended_message
        if self.hard_exceeded():
            return config.hard_limit_exceeded_message
        if self.hourly_exceeded():
            return config.hourly_limit_exceeded_message
        if self.soft_exceeded():
            return config.soft_limit_exceeded_message
        return None

    def can_send_feedback(self) -> bool:
        """Returns True if the user can continue in the feedback loop (i.e.
        is not blocked by hard, hourly, or soft limits).
        """
        if self.hard_exceeded():
            return False
        if self.hourly_exceeded():
            return False
        if self.soft_exceeded():
            return False
        return True

    def usage(self) -> float:
        """Returns the weekly usage as a fraction of the soft token limit."""
        return self._db.get_activity(
            time_delta={'days': config.soft_token_range}
        ) / config.soft_token_limit
