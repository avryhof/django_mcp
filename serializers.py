import json
from django.core.exceptions import ValidationError as DjangoValidationError


class MCPField:

    def __init__(self, required=True, default=None, help_text=""):
        self.required = required
        self.default = default
        self.help_text = help_text

    def to_schema(self):
        raise NotImplementedError

    def validate(self, value):
        return value

    def run_validation(self, value):
        if value is None and self.required and self.default is None:
            raise ValueError("This field is required.")
        if value is None and self.default is not None:
            return self.default
        return self.validate(value)

    def to_representation(self, value):
        return value


class CharField(MCPField):

    def __init__(self, **kwargs):
        self.max_length = kwargs.pop("max_length", None)
        super().__init__(**kwargs)

    def to_schema(self):
        schema = {"type": "string"}
        if self.max_length:
            schema["maxLength"] = self.max_length
        if self.help_text:
            schema["description"] = self.help_text
        return schema

    def validate(self, value):
        if not isinstance(value, str):
            raise ValueError("Expected a string.")
        if self.max_length and len(value) > self.max_length:
            raise ValueError(f"Must be no longer than {self.max_length} characters.")
        return value


class IntegerField(MCPField):

    def to_schema(self):
        schema = {"type": "integer"}
        if self.help_text:
            schema["description"] = self.help_text
        return schema

    def validate(self, value):
        if not isinstance(value, int):
            raise ValueError("Expected an integer.")
        return value


class FloatField(MCPField):

    def to_schema(self):
        schema = {"type": "number"}
        if self.help_text:
            schema["description"] = self.help_text
        return schema

    def validate(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Expected a number.")
        return value


class BooleanField(MCPField):

    def to_schema(self):
        schema = {"type": "boolean"}
        if self.help_text:
            schema["description"] = self.help_text
        return schema

    def validate(self, value):
        if not isinstance(value, bool):
            raise ValueError("Expected a boolean.")
        return value


class ListField(MCPField):

    def __init__(self, child=None, **kwargs):
        self.child = child or CharField()
        super().__init__(**kwargs)

    def to_schema(self):
        schema = {
            "type": "array",
            "items": self.child.to_schema(),
        }
        if self.help_text:
            schema["description"] = self.help_text
        return schema

    def validate(self, value):
        if not isinstance(value, list):
            raise ValueError("Expected a list.")
        return [self.child.validate(item) for item in value]


class DictField(MCPField):

    def to_schema(self):
        schema = {"type": "object"}
        if self.help_text:
            schema["description"] = self.help_text
        return schema

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValueError("Expected a dictionary.")
        return value


class ReadOnlyField(MCPField):

    def __init__(self, source=None, **kwargs):
        self.source = source
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_schema(self):
        return {"type": "string"}

    def validate(self, value):
        return value


class SerializerMethodField(MCPField):

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_schema(self):
        return {"type": "string"}

    def validate(self, value):
        return value


class StringRelatedField(MCPField):

    def __init__(self, source=None, many=False, **kwargs):
        self.source = source
        self.many = many
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_schema(self):
        return {"type": "string"}

    def validate(self, value):
        if value is None:
            return value
        if self.many:
            return [str(item) for item in value]
        return str(value)

    def to_representation(self, value):
        if value is None:
            return None
        if self.many:
            return [str(item) for item in value.all()]
        return str(value)


class NestedSerializerField(MCPField):

    def __init__(self, serializer_class, source=None, many=False, **kwargs):
        self.serializer_class = serializer_class
        self.source = source
        self.many = many
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_schema(self):
        return {"type": "object"}

    def validate(self, value):
        return value

    def to_representation(self, value):
        if value is None:
            return None
        if self.many:
            return self.serializer_class(instance=value.all(), many=True).data
        return self.serializer_class(instance=value).data


class Serializer:

    def __init__(self, instance=None, data=None, many=False):
        self.instance = instance
        self.initial_data = data
        self.many = many
        self.validated_data = {}
        self._errors = {}
        self.fields = self._get_fields()

    def _get_fields(self):
        fields = {}
        for name in dir(self.__class__):
            obj = getattr(self.__class__, name)
            if isinstance(obj, MCPField):
                fields[name] = obj
        return fields

    def to_schema(self):
        properties = {}
        required = []
        for name, field in self.fields.items():
            properties[name] = field.to_schema()
            if field.required:
                required.append(name)

        schema = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required
        return schema

    def validate(self, data):
        return data

    def is_valid(self):
        self._errors = {}
        self.validated_data = {}

        data = self.initial_data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                self._errors = {"non_field_errors": ["Invalid JSON."]}
                return False

        if not isinstance(data, dict):
            self._errors = {"non_field_errors": ["Expected a dictionary."]}
            return False

        for name, field in self.fields.items():
            value = data.get(name)
            try:
                validated = field.run_validation(value)
                self.validated_data[name] = validated
            except ValueError as exc:
                self._errors[name] = [str(exc)]

        try:
            self.validated_data = self.validate(self.validated_data)
        except DjangoValidationError as exc:
            self._errors.update(exc.message_dict)
        except ValueError as exc:
            self._errors["non_field_errors"] = [str(exc)]

        return not self._errors

    @property
    def errors(self):
        return self._errors

    @property
    def data(self):
        if self.instance is None:
            return {}
        if self.many:
            return [self.to_representation(item) for item in self.instance]
        return self.to_representation(self.instance)

    def to_representation(self, instance):
        ret = {}
        for name, field in self.fields.items():
            value = self._get_value(instance, name)
            ret[name] = field.to_representation(value)
        return ret

    def _get_value(self, instance, name):
        field = self.fields[name]
        if isinstance(field, SerializerMethodField):
            method_name = field.method_name or f"get_{name}"
            method = getattr(self, method_name, None)
            if method:
                return method(instance)
            return None
        source = getattr(field, "source", None) or name
        return self._get_attribute(instance, source)

    @staticmethod
    def _get_attribute(instance, source):
        if "." in source:
            obj = instance
            for part in source.split("."):
                obj = getattr(obj, part, None)
                if obj is None:
                    return None
            return obj
        return getattr(instance, source, None)
