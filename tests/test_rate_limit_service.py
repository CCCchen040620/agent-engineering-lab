from backend.services.rate_limit_service import InMemoryRateLimiter


def test_rate_limiter_allows_requests_within_limit():
    current_time = 100.0
    limiter = InMemoryRateLimiter(
        max_requests=2,
        window_seconds=60,
        time_provider=lambda: current_time,
    )

    first_result = limiter.check("client-a")
    second_result = limiter.check("client-a")

    assert first_result["allowed"] is True
    assert second_result["allowed"] is True


def test_rate_limiter_blocks_requests_over_limit():
    current_time = 100.0
    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
        time_provider=lambda: current_time,
    )

    first_result = limiter.check("client-a")
    second_result = limiter.check("client-a")

    assert first_result["allowed"] is True
    assert second_result["allowed"] is False
    assert second_result["retry_after_seconds"] == 60


def test_rate_limiter_allows_again_after_window():
    current_time = 100.0

    def get_time():
        return current_time

    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
        time_provider=get_time,
    )

    first_result = limiter.check("client-a")

    current_time = 161.0

    second_result = limiter.check("client-a")

    assert first_result["allowed"] is True
    assert second_result["allowed"] is True


def test_rate_limiter_uses_independent_keys():
    current_time = 100.0
    limiter = InMemoryRateLimiter(
        max_requests=1,
        window_seconds=60,
        time_provider=lambda: current_time,
    )

    first_result = limiter.check("client-a")
    second_result = limiter.check("client-b")

    assert first_result["allowed"] is True
    assert second_result["allowed"] is True
