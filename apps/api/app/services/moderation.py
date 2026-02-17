import re

BANNED_TERMS = {
    "kill yourself",
    "die",
    "i will hurt you",
}

SAFE_FALLBACK = "Message redacted by guardrails. Agent retries with a cleaner take."


def moderate_text(text: str) -> tuple[str, bool]:
    lowered = text.lower()
    for phrase in BANNED_TERMS:
        if phrase in lowered:
            return SAFE_FALLBACK, True
    if re.search(r"\b(?:idiot|moron)\b", lowered):
        return SAFE_FALLBACK, True
    return text, False
