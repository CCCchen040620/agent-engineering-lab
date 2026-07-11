import time
from collections.abc import Callable


class InMemoryRateLimiter:
    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        time_provider: Callable[[], float] | None = None,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.time_provider = time_provider or time.monotonic
        self.requests: dict[str, list[float]] = {}

    def check(self, key: str) -> dict:
        now = self.time_provider()
        window_start = now - self.window_seconds

        timestamps = [
            timestamp
            for timestamp in self.requests.get(key, [])
            if timestamp > window_start
        ]

        if len(timestamps) >= self.max_requests:
            oldest_timestamp = timestamps[0]
            retry_after_seconds = int(
                oldest_timestamp + self.window_seconds - now
            )

            self.requests[key] = timestamps

            return {
                "allowed": False,
                "retry_after_seconds": max(retry_after_seconds, 1),
            }

        timestamps.append(now)
        self.requests[key] = timestamps

        return {
            "allowed": True,
            "retry_after_seconds": 0,
        }
