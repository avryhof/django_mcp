import inspect


def generate_schema(func, input_serializer=None):
    if input_serializer is not None:
        serializer_instance = input_serializer()
        return serializer_instance.to_schema()

    sig = inspect.signature(func)
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name in ("request", "context", "self"):
            continue

        prop = _python_type_to_json_schema(param.annotation)
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


def _python_type_to_json_schema(annotation):
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
