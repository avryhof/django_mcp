import inspect

from .base import MCPTool


class FunctionTool(MCPTool):

    def __init__(self, func, name=None, description=None, input_serializer=None, permissions=None, tags=None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self.input_serializer = input_serializer
        self.permission_classes = permissions or []
        self.tags = tags or []
        self._is_async = inspect.iscoroutinefunction(func)

    def get_schema(self):
        if self.input_serializer is not None:
            serializer = self.input_serializer()
            return serializer.to_schema()

        sig = inspect.signature(self.func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("request", "context"):
                continue

            prop = self._python_type_to_json_schema(param.annotation)
            properties[param_name] = prop

            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        schema = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required
        return schema

    def execute(self, request, **kwargs):
        if self._is_async:
            raise RuntimeError(
                f"Tool '{self.name}' is async. Use aexecute() instead."
            )
        return self.func(request, **kwargs)

    async def aexecute(self, request, **kwargs):
        if self._is_async:
            return await self.func(request, **kwargs)
        return self.func(request, **kwargs)

    def to_tool_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.get_schema(),
        }
