import re


def extract_valid_urls(inputs: str | list[str]) -> str | list[str] | None:
    pattern = re.compile(r"https?://\S+")
    if isinstance(inputs, str):
        match = pattern.search(inputs)
        return match.group(0) if match else None

    urls: list[str] = []
    for item in inputs:
        urls.extend(pattern.findall(item))
    return urls
