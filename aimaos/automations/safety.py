from __future__ import annotations


BLOCKED_AUTOMATION_PATTERNS = [
    "captcha",
    "2fa bypass",
    "security bypass",
    "policy bypass",
]


def assert_allowed_automation(action_description: str) -> None:
    normalized = action_description.lower()
    for pattern in BLOCKED_AUTOMATION_PATTERNS:
        if pattern in normalized:
            raise ValueError(f"허용되지 않는 자동화 요청입니다: {pattern}")

