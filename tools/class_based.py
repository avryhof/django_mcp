import inspect

from .base import MCPTool


class ClassBasedTool(MCPTool):

    def __init__(self):
        self._setup()

    def _setup(self):
        pass

    def get_schema(self):
        if self.input_serializer is not None:
            serializer = self.input_serializer()
            return serializer.to_schema()

        execute_method = self.execute
        sig = inspect.signature(execute_method)

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "request", "context"):
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
        raise NotImplementedError("Subclasses must implement execute()")

    async def aexecute(self, request, **kwargs):
        return self.execute(request, **kwargs)

    def to_tool_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.get_schema(),
        }
