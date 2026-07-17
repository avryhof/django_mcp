import functools
import inspect
import logging

from .registry import registry
from .schemas import generate_schema

logger = logging.getLogger("django_mcp")


def tool(
    func=None,
    *,
    name=None,
    description=None,
    input_serializer=None,
    permissions=None,
    tags=None
):
    def decorator(fn):
        tool_name = name or fn.__name__
        tool_description = description or fn.__doc__ or ""
        schema = generate_schema(fn, input_serializer=input_serializer)

        is_async = inspect.iscoroutinefunction(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper._mcp_tool = True
        wrapper._mcp_tool_name = tool_name
        wrapper._mcp_tool_description = tool_description
        wrapper._mcp_input_serializer = input_serializer
        wrapper._mcp_permissions = permissions or []
        wrapper._mcp_tags = tags or []
        wrapper._mcp_schema = schema
        wrapper._mcp_is_async = is_async

        registry.register(
            wrapper,
            name=tool_name,
            description=tool_description,
            input_serializer=input_serializer,
            permissions=permissions or [],
            tags=tags or [],
        )

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator


mcp_tool = tool
