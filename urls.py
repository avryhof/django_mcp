from django.urls import path
from .views import MCPStreamableHTTPView, MCPSSEView, MCPToolListView, MCPClientCredentialsView

urlpatterns = [
    path(
        "",
        MCPStreamableHTTPView.as_view(),
        name="mcp-endpoint",
    ),
    path(
        "tools/",
        MCPToolListView.as_view(),
        name="mcp-tools-list",
    ),
    path(
        "sse/",
        MCPSSEView.as_view(),
        name="mcp-sse",
    ),
    path(
        "credentials/",
        MCPClientCredentialsView.as_view(),
        name="mcp-credentials",
    ),
]
