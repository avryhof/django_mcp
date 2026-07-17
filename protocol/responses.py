import json


class MCPResponse:

    def __init__(self, result=None, error=None, id=None):
        self.jsonrpc = "2.0"
        self.result = result
        self.error = error
        self.id = id

    @classmethod
    def success(cls, result, id=None):
        return cls(result=result, id=id)

    @classmethod
    def error_response(cls, error, id=None):
        return cls(error=error, id=id)

    def to_dict(self):
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
        }
        if self.error is not None:
            result["error"] = self.error
        else:
            result["result"] = self.result
        return result

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_http_response(self):
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            **(
                {"error": self.error}
                if self.error is not None
                else {"result": self.result}
            ),
        }
