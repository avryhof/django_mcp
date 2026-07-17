from .errors import MCPError, InternalError, ParseError
from .requests import MCPRequest
from .responses import MCPResponse


class JSONRPCHandler:

    def __init__(self):
        self._methods = {}

    def register(self, method_name, handler):
        self._methods[method_name] = handler

    def handle(self, raw_data):
        try:
            request = MCPRequest.from_bytes(raw_data)
        except (ValueError, TypeError) as exc:
            error = ParseError(str(exc))
            return MCPResponse.error_response(error.to_dict(), id=None)

        try:
            return self._dispatch(request)
        except MCPError as exc:
            return MCPResponse.error_response(exc.to_dict(), id=request.id)
        except Exception as exc:
            error = InternalError(str(exc))
            return MCPResponse.error_response(error.to_dict(), id=request.id)

    def _dispatch(self, request):
        handler = self._methods.get(request.method)
        if handler is None:
            from .errors import MethodNotFound
            raise MethodNotFound(request.method)

        result = handler(request)

        if request.is_notification:
            return None

        if isinstance(result, MCPResponse):
            return result

        return MCPResponse.success(result=result, id=request.id)
