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


class Serializer:

    def __init__(self, data=None):
        self.initial_data = data
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
