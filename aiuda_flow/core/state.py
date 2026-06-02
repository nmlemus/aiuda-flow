from typing import Any, Optional
from typing_extensions import TypedDict, Annotated
import operator


class BaseState(TypedDict, total=False):
    """Base state schema for all aiuda-flow graphs."""
    messages: Annotated[list[Any], operator.add]
    context: dict[str, Any]
    error: Optional[str]
    metadata: dict[str, Any]
