from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import sleep as _sleep
from typing import Callable, TypeVar

ROUTE_A_PROVIDER_MAX_ATTEMPTS = 3
ROUTE_A_PROVIDER_BACKOFF_SECONDS = (0.1, 0.2)
ROUTE_A_PROVIDER_JITTER_ENABLED = False
ROUTE_A_PROVIDER_SDK_OPTIONS = {"max_retries": 0}

_FAIL_FAST_EXCEPTION_NAMES = frozenset(
    {
        "AuthenticationError",
        "BadRequestError",
        "ConflictError",
        "NotFoundError",
        "PermissionDeniedError",
        "UnprocessableEntityError",
        "UnsupportedProviderError",
    }
)
_RETRYABLE_EXCEPTION_NAMES = frozenset(
    {
        "APIConnectionError",
        "APITimeoutError",
        "InternalServerError",
        "RateLimitError",
    }
)

T = TypeVar("T")


class RouteAErrorDisposition(str, Enum):
    RETRYABLE = "retryable"
    FAIL_FAST = "fail_fast"


@dataclass(frozen=True, slots=True)
class RouteAResiliencePolicy:
    max_attempts: int = ROUTE_A_PROVIDER_MAX_ATTEMPTS
    backoff_seconds: tuple[float, ...] = ROUTE_A_PROVIDER_BACKOFF_SECONDS
    jitter_enabled: bool = ROUTE_A_PROVIDER_JITTER_ENABLED

    def __post_init__(self) -> None:
        if self.max_attempts != len(self.backoff_seconds) + 1:
            raise ValueError(
                "Route A resilience policy requires one fewer backoff than attempts"
            )


@dataclass(frozen=True, slots=True)
class RouteAResilienceDecision:
    disposition: RouteAErrorDisposition
    reason: str


def classify_route_a_provider_error(exc: BaseException) -> RouteAResilienceDecision:
    if isinstance(exc, (TypeError, ValueError)):
        return RouteAResilienceDecision(
            RouteAErrorDisposition.FAIL_FAST, "invalid_request"
        )

    exception_name = type(exc).__name__
    if exception_name in _RETRYABLE_EXCEPTION_NAMES:
        return RouteAResilienceDecision(
            RouteAErrorDisposition.RETRYABLE, exception_name
        )
    if exception_name in _FAIL_FAST_EXCEPTION_NAMES:
        return RouteAResilienceDecision(
            RouteAErrorDisposition.FAIL_FAST, exception_name
        )

    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return RouteAResilienceDecision(
            RouteAErrorDisposition.RETRYABLE, "status_code_429"
        )
    if isinstance(status_code, int) and status_code >= 500:
        return RouteAResilienceDecision(
            RouteAErrorDisposition.RETRYABLE, f"status_code_{status_code}"
        )
    if status_code in {400, 401, 403, 404, 409, 422}:
        return RouteAResilienceDecision(
            RouteAErrorDisposition.FAIL_FAST, f"status_code_{status_code}"
        )

    return RouteAResilienceDecision(
        RouteAErrorDisposition.FAIL_FAST, exception_name or "unknown"
    )


def is_route_a_retryable_provider_error(exc: BaseException) -> bool:
    return (
        classify_route_a_provider_error(exc).disposition
        is RouteAErrorDisposition.RETRYABLE
    )


def route_a_provider_sdk_options() -> dict[str, int]:
    return dict(ROUTE_A_PROVIDER_SDK_OPTIONS)


def run_with_route_a_provider_resilience(
    operation: Callable[[], T],
    *,
    policy: RouteAResiliencePolicy = RouteAResiliencePolicy(),
    sleep: Callable[[float], None] = _sleep,
) -> T:
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return operation()
        except Exception as exc:
            decision = classify_route_a_provider_error(exc)
            should_retry = (
                decision.disposition is RouteAErrorDisposition.RETRYABLE
                and attempt < policy.max_attempts
            )
            if not should_retry:
                raise
            sleep(policy.backoff_seconds[attempt - 1])

    raise AssertionError("Route A provider resilience exhausted without result")


__all__ = [
    "ROUTE_A_PROVIDER_BACKOFF_SECONDS",
    "ROUTE_A_PROVIDER_JITTER_ENABLED",
    "ROUTE_A_PROVIDER_MAX_ATTEMPTS",
    "RouteAErrorDisposition",
    "RouteAResilienceDecision",
    "RouteAResiliencePolicy",
    "classify_route_a_provider_error",
    "is_route_a_retryable_provider_error",
    "route_a_provider_sdk_options",
    "run_with_route_a_provider_resilience",
]
