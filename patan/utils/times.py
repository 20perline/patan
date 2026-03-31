import datetime as dt


def get_timestamp(unit: str = "milli") -> int:
    now = dt.datetime.now(tz=dt.UTC)
    seconds = int(now.timestamp())
    if unit == "milli":
        return int(now.timestamp() * 1000)
    if unit == "sec":
        return seconds
    if unit == "min":
        return seconds // 60
    raise ValueError(f"unsupported time unit: {unit}")


def timestamp_2_str(timestamp: str | int | float, format: str = "%Y-%m-%d %H-%M-%S") -> str:
    if timestamp in {None, "None"}:
        return ""
    if isinstance(timestamp, str) and len(timestamp) == 30:
        return str(dt.datetime.strptime(timestamp, "%a %b %d %H:%M:%S %z %Y"))
    return dt.datetime.fromtimestamp(float(timestamp)).strftime(format)
