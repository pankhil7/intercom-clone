import bleach
import re
from better_profanity import profanity

ALLOWED_TAGS = ['p', 'b', 'i', 'u', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'br', 'span', 'h1', 'h2', 'h3', 'blockquote', 'code', 'pre']


def sanitize_html(text: str) -> str:
    """Strip dangerous HTML, allow safe formatting tags."""
    return bleach.clean(text, tags=ALLOWED_TAGS, strip=True)


def strip_html(text: str) -> str:
    """Remove all HTML tags, return plain text."""
    return bleach.clean(text, tags=[], strip=True)


def sanitize_string(text: str) -> str:
    """Strip all HTML from a string (for LLM outputs)."""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()


def sanitize_dict_strings(data: dict) -> dict:
    """Recursively sanitize all string values in a dict."""
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = sanitize_string(v)
        elif isinstance(v, list):
            result[k] = [sanitize_string(i) if isinstance(i, str) else i for i in v]
        else:
            result[k] = v
    return result


def apply_profanity_filter(text: str) -> str:
    """Return None if profanity detected, else return text."""
    if profanity.contains_profanity(text):
        return None
    return text


def extract_urls(text: str) -> list:
    pattern = r'https?://[^\s<>"\'()]+'
    return re.findall(pattern, text)


def strip_unverified_urls(text: str, allowed_urls: list) -> str:
    """Remove URLs from text that are not in the allowed list."""
    def replace_url(match):
        url = match.group(0)
        if any(url.startswith(allowed) for allowed in allowed_urls):
            return url
        return '[link removed]'
    return re.sub(r'https?://[^\s<>"\'()]+', replace_url, text)
