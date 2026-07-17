import json


class MCPRequest:

    def __init__(self, jsonrpc="2.0", method=None, params=None, id=None):
        self.jsonrpc = jsonrpc
        self.method = method
        self.params = params or {}
        self.id = id

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Request must be a dictionary")

        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method"),
            params=data.get("params", {}),
            id=data.get("id"),
        )

    @classmethod
    def from_bytes(cls, raw):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc

        return cls.from_dict(data)

    @property
    def is_notification(self):
        return self.id is None

    def to_dict(self):
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params,
        }
        if self.id is not None:
            result["id"] = self.id
        return result
