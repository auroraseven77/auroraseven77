from __future__ import annotations

from urllib.parse import urlparse


class AuthorizationError(ValueError):
    """Raised when a target is outside the explicitly supplied scope."""


def normalize_target(target: str) -> str:
    value = target.strip()
    if not value:
        raise AuthorizationError("empty target")
    if "://" in value:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise AuthorizationError("only valid HTTP(S) URLs are accepted")
        return parsed.hostname.lower()
    return value.lower().rstrip(".")


def authorize(target: str, allowed: list[str] | tuple[str, ...] | None) -> str:
    """Require an explicit allow-list for collection.

    A missing/empty allow-list denies execution. Subdomains are accepted only
    when their parent domain is explicitly listed.
    """
    normalized = normalize_target(target)
    if not allowed:
        raise AuthorizationError("no authorized targets configured")
    scopes = {normalize_target(item) for item in allowed}
    if normalized not in scopes and not any(normalized.endswith("." + scope) for scope in scopes):
        raise AuthorizationError(f"target outside authorized scope: {normalized}")
    return normalized
