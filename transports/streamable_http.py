import json
import logging

from django.http import JsonResponse

from ..authentication import ClientCredentialsAuthentication
from ..protocol.jsonrpc import JSONRPCHandler
from ..protocol.responses import MCPResponse
from ..context import set_context, get_context, clear_context

logger = logging.getLogger("django_mcp")

_client_auth = ClientCredentialsAuthentication()


def _get_enabled_tool_names():
    """Return the set of enabled tool names from MCPToolConfig.
    Falls back to all tools if the model doesn't exist yet (e.g. during migration)."""
    try:
        from ..models import MCPToolConfig
        return set(MCPToolConfig.objects.filter(enabled=True).values_list("name", flat=True))
    except Exception:
        # Model may not exist yet during migrations or if DB is not ready
        from ..registry import registry
        return set(registry.list().keys())


class StreamableHTTPTransport:

    def __init__(self):
        self.handler = JSONRPCHandler()
        self._register_methods()

    def _register_methods(self):
        self.handler.register("tools/list", self._handle_tools_list)
        self.handler.register("tools/call", self._handle_tools_call)
        self.handler.register("initialize", self._handle_initialize)
        self.handler.register("ping", self._handle_ping)

    def _handle_initialize(self, request):
        from django.conf import settings

        server_name = getattr(settings, "MCP_SERVER_NAME", "django-mcp")
        return {
            "protocolVersion": "2025-03-26",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": server_name,
                "version": "0.1.0",
            },
        }

    def _handle_ping(self, request):
        return {}

    def _handle_tools_list(self, request):
        from ..registry import registry

        enabled_names = _get_enabled_tool_names()
        tools = registry.list()
        return {
            "tools": [tool.to_tool_dict() for name, tool in tools.items() if name in enabled_names],
        }

    def _handle_tools_call(self, request):
        from ..registry import registry
        from ..exceptions import ToolPermissionDenied, ToolValidationError

        params = request.params
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Check if tool is enabled
        enabled_names = _get_enabled_tool_names()
        if tool_name not in enabled_names:
            return MCPResponse.error_response(
                {
                    "code": -32601,
                    "message": f"Tool '{tool_name}' is not enabled.",
                },
                id=request.id,
            ).to_dict()

        try:
            tool = registry.get(tool_name)
        except Exception as exc:
            return MCPResponse.error_response(
                {
                    "code": -32601,
                    "message": str(exc),
                },
                id=request.id,
            ).to_dict()

        django_request = get_context()

        for permission_class in tool.permission_classes:
            if callable(permission_class):
                perm = permission_class()
            else:
                perm = permission_class
            if not perm.has_permission(django_request, tool):
                return MCPResponse.error_response(
                    {
                        "code": -32601,
                        "message": f"Permission denied for tool '{tool_name}'.",
                    },
                    id=request.id,
                ).to_dict()

        if tool.input_serializer is not None:
            serializer = tool.input_serializer(data=arguments)
            if not serializer.is_valid():
                return MCPResponse.error_response(
                    {
                        "code": -32602,
                        "message": f"Invalid arguments for tool '{tool_name}': {serializer.errors}",
                    },
                    id=request.id,
                ).to_dict()
            validated_data = serializer.validated_data
        else:
            validated_data = arguments

        try:
            import asyncio

            if getattr(tool, "_is_async", False):
                result = asyncio.run(
                    tool.aexecute(django_request, **validated_data)
                )
            else:
                result = tool.execute(django_request, **validated_data)
        except Exception as exc:
            logger.exception("Error executing tool '%s'", tool_name)
            return MCPResponse.error_response(
                {
                    "code": -32603,
                    "message": f"Error executing tool: {exc}",
                },
                id=request.id,
            ).to_dict()

        if isinstance(result, dict):
            content = json.dumps(result)
        elif isinstance(result, list):
            content = json.dumps(result)
        else:
            content = str(result)

        return {
            "content": [
                {
                    "type": "text",
                    "text": content,
                }
            ],
        }

    def _authenticate(self, request):
        user = _client_auth.authenticate(request)
        if user is not None:
            request.user = user

    def handle_get(self, request):
        from ..registry import registry

        self._authenticate(request)
        enabled_names = _get_enabled_tool_names()
        tools = registry.list()
        tools_list = [tool.to_tool_dict() for name, tool in tools.items() if name in enabled_names]

        return JsonResponse(
            {
                "jsonrpc": "2.0",
                "id": "1",
                "result": {
                    "tools": tools_list,
                },
            },
            json_dumps_params={"indent": 2},
        )

    def handle_post(self, request):
        try:
            raw_data = request.body
        except Exception:
            return JsonResponse(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error",
                    },
                },
                status=400,
            )

        try:
            request_data = json.loads(raw_data)
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error: Invalid JSON",
                    },
                },
                status=400,
            )

        self._authenticate(request)
        set_context(django_request=request)
        try:
            if isinstance(request_data, list):
                responses = []
                for item in request_data:
                    response = self.handler.handle(json.dumps(item).encode())
                    if response is not None:
                        responses.append(response.to_dict())
                return JsonResponse(responses, safe=False, json_dumps_params={"indent": 2})

            response = self.handler.handle(json.dumps(request_data).encode())

            if response is None:
                return JsonResponse({}, status=202)

            return JsonResponse(response.to_dict(), json_dumps_params={"indent": 2})
        finally:
            clear_context()

    def handle_delete(self, request):
        return JsonResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32600,
                    "message": "Not supported",
                },
            },
            status=405,
        )
