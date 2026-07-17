class MCPError(Exception):

    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    def to_dict(self):
        error = {
            "code": self.code,
            "message": self.message,
        }
        if self.data is not None:
            error["data"] = self.data
        return error


class ParseError(MCPError):

    def __init__(self, message="Parse error", data=None):
        super().__init__(code=-32700, message=message, data=data)


class InvalidRequest(MCPError):

    def __init__(self, message="Invalid request", data=None):
        super().__init__(code=-32600, message=message, data=data)


class MethodNotFound(MCPError):

    def __init__(self, method, data=None):
        message = f"Method not found: {method}"
        super().__init__(code=-32601, message=message, data=data)


class InvalidParams(MCPError):

    def __init__(self, message="Invalid params", data=None):
        super().__init__(code=-32602, message=message, data=data)


class InternalError(MCPError):

    def __init__(self, message="Internal error", data=None):
        super().__init__(code=-32603, message=message, data=data)


class ToolNotFound(MCPError):

    def __init__(self, tool_name, data=None):
        message = f"Tool not found: {tool_name}"
        super().__init__(code=-32601, message=message, data=data)


class ToolPermissionDenied(MCPError):

    def __init__(self, tool_name, data=None):
        message = f"Permission denied for tool: {tool_name}"
        super().__init__(code=-32601, message=message, data=data)


class ToolExecutionError(MCPError):

    def __init__(self, tool_name, message="Tool execution failed", data=None):
        full_message = f"Error executing tool '{tool_name}': {message}"
        super().__init__(code=-32603, message=full_message, data=data)
