# django-mcp

A Django-native Model Context Protocol framework. Expose Django applications through MCP without FastMCP, FastAPI, separate processes, or duplicated authentication.

## Requirements

- Python 3.10+
- Django 4.2+

## Installation

1. Copy the `django_mcp` directory into your Django project (or install via your preferred method).
2. Add `"django_mcp"` to `INSTALLED_APPS`.
3. Include the MCP URLs in your root URL configuration.

```python
# settings.py
INSTALLED_APPS = [
    "...",
    "django_mcp",
]

# urls.py
from django.urls import path, include

urlpatterns = [
    path("mcp/", include("django_mcp.urls")),
]
```

That's it. No additional configuration is required.

## Creating Tools

### Function-Based Tools

Create an `mcp_tools.py` file in any Django app:

```python
# members/mcp_tools.py
from django_mcp import tool

@tool
def get_member_count(request):
    return {"count": 42}
```

The function name becomes the tool name. The first argument is always the Django `request` object.

### Named Tools

```python
from django_mcp import tool

@tool(
    name="member_lookup",
    description="Lookup member information by ID",
)
def member_lookup(request, member_id: str):
    return {"member_id": member_id, "name": "Jane Doe"}
```

### With Permissions

```python
from django_mcp import tool, IsAuthenticated, DjangoPermission

@tool(
    name="admin_report",
    permissions=[IsAuthenticated]
)
def admin_report(request):
    return {"report": "data"}

@tool(
    name="delete_member",
    permissions=[
        IsAuthenticated,
        DjangoPermission("members.delete_member"),
    ]
)
def delete_member(request, member_id: str):
    return {"result": "ok"}
```

### With Serializers

```python
from django_mcp import tool, Serializer, CharField, IntegerField

class MemberLookupSerializer(Serializer):
    member_id = CharField()
    radius = IntegerField(required=False, default=10)

@tool(name="member_search", input_serializer=MemberLookupSerializer)
def member_search(request, validated_data):
    return {"results": []}
```

### Async Tools

```python
from django_mcp import tool

async def some_async_operation(query):
    return []

@tool
async def search_items(request, query: str):
    results = await some_async_operation(query)
    return {"results": results}
```

### Tool Options

The `@tool` decorator accepts:

| Parameter | Type | Description |
|---|---|---|
| `name` | str | Tool name (defaults to function name) |
| `description` | str | Tool description (defaults to docstring) |
| `input_serializer` | Serializer | Serializer class for input validation |
| `permissions` | list | Permission classes to check before execution |
| `tags` | list | Tags for grouping/filtering |

## Permission Classes

| Class | Description |
|---|---|
| `IsAuthenticated` | User must be authenticated |
| `IsAnonymous` | User must be anonymous |
| `AllowAny` | Allows any request |
| `DenyAll` | Denies all requests |
| `IsSuperUser` | User must be a superuser |
| `IsStaff` | User must be staff |
| `DjangoPermission("app.label")` | Checks a specific Django permission |
| `IsInGroup("group_name")` | User must be in the named group |

### Custom Permissions

```python
from django_mcp.permissions import MCPPermission

class IsTeamLeader(MCPPermission):
    def has_permission(self, request, tool):
        return request.user.groups.filter(name="TeamLeader").exists()
```

## Serializers

DRF-inspired serializer system for input validation and schema generation.

```python
from django_mcp import Serializer, CharField, IntegerField, BooleanField, ListField

class SearchSerializer(Serializer):
    query = CharField(max_length=100)
    page = IntegerField(required=False, default=1)
    active_only = BooleanField(required=False, default=True)
    tags = ListField(required=False)
```

### Available Fields

| Field | Type | Options |
|---|---|---|
| `CharField` | string | `max_length` |
| `IntegerField` | integer | |
| `FloatField` | number | |
| `BooleanField` | boolean | |
| `ListField` | array | `child` (field instance) |
| `DictField` | object | |

### Schema Generation

Schemas are generated automatically from serializers or from function type hints:

```python
from django_mcp import tool

# Type hints
@tool
def add(request, a: int, b: int):
    return {"result": a + b}

# Produces:
# {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}
```

## Class-Based Tools

```python
from django_mcp import MCPTool, IsAuthenticated

class MemberLookupTool(MCPTool):
    name = "member_lookup"
    description = "Lookup member information"
    permission_classes = [IsAuthenticated]

    def execute(self, request, member_id: str):
        return {"member_id": member_id}
```

Async variant:

```python
from django_mcp import MCPTool

async def some_async_operation(query):
    return []

class AsyncSearchTool(MCPTool):
    name = "async_search"

    async def execute(self, request, query: str):
        results = await some_async_operation(query)
        return {"results": results}
```

## App-Based Discovery

Each Django app can define its own `mcp_tools.py`. The framework automatically discovers and registers tools from all installed apps during startup.

```
members/
├── models.py
├── views.py
├── urls.py
└── mcp_tools.py    # Tools defined here are auto-discovered
```

No manual registration is required. If an app has a `mcp_tools.py` module, its tools are loaded automatically.

## URL Routing

### Default (Recommended)

```python
from django.urls import path, include

urlpatterns = [
    path("mcp/", include("django_mcp.urls")),
]
```

This exposes:

| Endpoint | Method | Description |
|---|---|---|
| `/mcp/` | GET | List all registered tools |
| `/mcp/` | POST | Execute JSON-RPC requests |
| `/mcp/sse/` | GET | SSE transport (for older clients) |
| `/mcp/sse/` | POST | SSE transport RPC |

### MCPRouter

For per-app URL configuration:

```python
# members/mcp_urls.py
from django_mcp import MCPRouter

router = MCPRouter()
router.register_tool("member_lookup")
router.register_tool("member_search")

urlpatterns = router.urls
```

## MCP Protocol

### JSON-RPC Methods

**initialize**

```json
{"jsonrpc": "2.0", "id": "1", "method": "initialize"}
```

Returns server info and capabilities.

**tools/list**

```json
{"jsonrpc": "2.0", "id": "1", "method": "tools/list"}
```

Returns all registered tools with schemas.

**tools/call**

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "member_lookup",
    "arguments": {"member_id": "12345"}
  }
}
```

Executes a tool and returns its result.

**ping**

```json
{"jsonrpc": "2.0", "id": "1", "method": "ping"}
```

Returns `{}`.

### Batch Requests

JSON-RPC batch requests (arrays) are supported:

```json
[
  {"jsonrpc": "2.0", "id": "1", "method": "tools/list"},
  {"jsonrpc": "2.0", "id": "2", "method": "ping"}
]
```

## Management Commands

```bash
python manage.py list_mcp_tools
```

Lists all registered tools with descriptions, schemas, and permissions.

## Transports

### Streamable HTTP (Primary)

The default transport. Uses standard HTTP POST for JSON-RPC communication.

### SSE (Optional)

Available at `/mcp/sse/` for clients that require Server-Sent Events. Feature flag coming in Phase 2.

## Context Objects

Tools receive the authenticated Django request, giving access to:

```python
from django_mcp import tool

@tool
def my_profile(request):
    return {
        "username": request.user.username,
        "email": request.user.email,
        "session_key": request.session.session_key,
        "is_ajax": request.headers.get("X-Requested-With") == "XMLHttpRequest",
    }
```

All middleware-injected data (e.g., `request.tenant`, `request.organization`) is available automatically.

## Settings

Optional settings (add to `settings.py`):

```python
# Enable SSE transport (default: True)
MCP_ENABLE_SSE = True

# Custom tool discovery apps (default: all INSTALLED_APPS)
MCP_DISCOVERY_APPS = []
```

## Example: Member Lookup tool

```python
# members/models.py
from django.conf import settings
from django.db import models

class Member(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    member_id = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)

# members/mcp_tools.py
from django_mcp import tool, Serializer, CharField, IsAuthenticated, DjangoPermission
class MemberLookupSerializer(Serializer):
    member_id = CharField()

@tool(
    name="member_lookup",
    description="Retrieve member demographic information",
    permissions=[IsAuthenticated, DjangoPermission("members.view_member")],
    input_serializer=MemberLookupSerializer,
)
def member_lookup(request, validated_data):
    member = Member.objects.get(member_id=validated_data["member_id"])
    return {
        "member_id": member.member_id,
        "first_name": member.first_name,
        "last_name": member.last_name,
    }
```

## License

MIT.

See [LICENSE](./LICENSE)
