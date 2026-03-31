from urllib.parse import urlencode

from pydantic import BaseModel


def model_to_query_string(model: BaseModel) -> str:
    return urlencode(model.model_dump())
