import json
import logging

from django.http import JsonResponse
from django.views import View

from .transports.streamable_http import StreamableHTTPTransport
from .transports.sse import SSETransport
from .registry import registry
from .protocol.errors import MCPError

logger = logging.getLogger("django_mcp")


class MCPStreamableHTTPView(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transport = StreamableHTTPTransport()

    def get(self, request, *args, **kwargs):
        return self.transport.handle_get(request)

    def post(self, request, *args, **kwargs):
        return self.transport.handle_post(request)

    def delete(self, request, *args, **kwargs):
        return self.transport.handle_delete(request)


class MCPSSEView(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transport = SSETransport()

    def get(self, request, *args, **kwargs):
        return self.transport.handle_sse(request)

    def post(self, request, *args, **kwargs):
        return self.transport.handle_post(request)


class MCPToolListView(View):

    def get(self, request, *args, **kwargs):
        tools = registry.list()
        tools_list = [tool.to_tool_dict() for tool in tools.values()]
        return JsonResponse(
            {"tools": tools_list},
            json_dumps_params={"indent": 2},
        )
