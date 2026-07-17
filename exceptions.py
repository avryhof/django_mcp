from django.core.exceptions import PermissionDenied


class MCPException(Exception):
    pass


class ToolNotFound(MCPException):
    pass


class ToolAlreadyRegistered(MCPException):
    pass


class ToolPermissionDenied(MCPException):
    pass


class ToolValidationError(MCPException):

    def __init__(self, errors):
        self.errors = errors
        super().__init__(f"Validation error: {errors}")


class ToolExecutionError(MCPException):

    def __init__(self, tool_name, original_error=None):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Error executing tool '{tool_name}'")


class TransportError(MCPException):
    pass


class InvalidRequest(MCPException):
    pass
