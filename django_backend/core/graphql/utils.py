def truncate_to_words(text: str, max_chars: int = 30) -> str:
    if not text or len(text) <= max_chars:
        return text

    truncated = text[:max_chars]

    last_space = truncated.rfind(" ")

    if last_space > 0:
        return truncated[:last_space] + "..."

    return truncated + "..."
