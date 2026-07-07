import logging
from . import config
logger = logging.getLogger('sigmund')


class LimitsChecker:
    """Centralized checks for all usage limits (hourly, weekly, and suspension).

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
        hourly_activity = self._db.get_activity(time_delta={'hours': 1})
        logger.info(f'hourly_activity: {hourly_activity}')
        return hourly_activity > config.hourly_token_limit

    def weekly_exceeded(self) -> bool:
        """Returns True if the weekly token limit has been exceeded
        AND the user has no activity buffer remaining.

        When the weekly limit is exceeded but a buffer is available, the user
        is allowed to continue (drawing from the buffer), so this returns
        False.
        """
        weekly_activity = self._db.get_activity(
            time_delta={'days': config.weekly_token_range}
        )
        logger.info(f'weekly_activity: {weekly_activity}')
        if weekly_activity < config.weekly_token_limit:
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
        over the weekly limit, and suspension takes the highest precedence.
        """
        if self.suspended():
            return config.suspended_message
        if self.hourly_exceeded():
            return config.hourly_limit_exceeded_message
        if self.weekly_exceeded():
            return config.weekly_limit_exceeded_message
        return None

    def can_send_feedback(self) -> bool:
        """Returns True if the user can continue in the feedback loop (i.e.
        is not blocked by hard, hourly, or weekly limits).
        """
        if self.hourly_exceeded():
            return False
        if self.weekly_exceeded():
            return False
        return True
        
    def weekly_credits_used(self) -> int:
        return self._db.get_activity(
            time_delta={'days': config.weekly_token_range}
        )

    def usage(self) -> float:
        """Returns the weekly usage as a fraction of the weekly token limit."""
        return self.weekly_credits_used() / config.weekly_token_limit

    def weekly_credits_left(self) -> int:
        return max(0, config.weekly_token_limit - self.weekly_credits_used())
        
    def extra_credits_left(self) -> int:
        return max(0, self._db.get_activity_buffer())
