from django.urls import path, include

from .views import MCPStreamableHTTPView, MCPSSEView

app_name = "django_mcp"

urlpatterns = [
    path(
        "",
        MCPStreamableHTTPView.as_view(),
        name="mcp-endpoint",
    ),
    path(
        "sse/",
        MCPSSEView.as_view(),
        name="mcp-sse",
    ),
]


class MCPRouter:

    def __init__(self, prefix=""):
        self.prefix = prefix
        self._tools = []
        self._custom_urls = []

    def register_tool(self, tool_name, name=None):
        from .registry import registry

        tool = registry.get(tool_name)
        self._tools.append(tool)
        return self

    def register(self, prefix, viewset, basename=None):
        self._custom_urls.append(
            path(f"{prefix}/", viewset.as_view(), name=basename)
        )
        return self

    @property
    def urls(self):
        return self._custom_urls, "mcp-router"
