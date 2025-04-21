from pprint import pformat

import pydantic


def ppformat(pmodel: pydantic.BaseModel) -> str:
    """Return a pretty string formatting a pydantic model."""
    return pformat(pmodel.model_dump())
