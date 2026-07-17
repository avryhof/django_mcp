import inspect

from ..schemas import generate_schema


class MCPTool:

    name = None
    description = ""
    input_serializer = None
    permission_classes = []
    tags = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.name is None:
            cls.name = cls.__name__

    def get_schema(self):
        if self.input_serializer is not None:
            serializer = self.input_serializer()
            return serializer.to_schema()

        execute_method = self.execute
        if hasattr(execute_method, "__func__"):
            sig = inspect.signature(execute_method)
        else:
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

    def _python_type_to_json_schema(self, annotation):
        if annotation is inspect.Parameter.empty:
            return {"type": "string"}

        type_map = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }
        return type_map.get(annotation, {"type": "string"})

    def to_tool_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.get_schema(),
        }

    def execute(self, request, **kwargs):
        raise NotImplementedError("Subclasses must implement execute()")

    async def aexecute(self, request, **kwargs):
        return self.execute(request, **kwargs)
