# django-mcp
## A Django-Native Model Context Protocol Framework

### Vision

Build a Django-native MCP framework that feels as natural to Django developers as Django REST Framework.

Instead of treating MCP as a standalone service that communicates with Django, `django-mcp` should make MCP a first-class citizen of the Django request lifecycle:

- Operates within Django's authentication framework
- Uses Django sessions
- Uses Django permissions
- Uses Django middleware
- Uses Django ORM
- Uses Django app discovery
- Supports Streamable HTTP
- Supports SSE (optional/backward compatibility)
- Supports synchronous and asynchronous tools
- Automatically generates MCP tool schemas


# Non-Goals

The following are intentionally outside the scope of django-mcp:

- User authentication
- Identity management
- Single sign-on implementations
- OAuth providers
- OpenID Connect providers
- SAML providers
- Session storage implementations

These concerns are already solved by Django and its ecosystem.

django-mcp should focus on exposing Django applications through the Model Context Protocol and should not duplicate functionality already provided by Django.


---

# Design Principles

## 1. Django First

The framework should prioritize Django conventions over MCP implementation details.

Good:

```python
from django_mcp import tool

@tool
def my_profile(request):
    return {
        "username": request.user.username
    }
```

Bad:

```python
from django_mcp.decorators import mcp_tool

# This won't work because request should be the first parameter, but @mcp tool is an alias of @tool
@mcp_tool
def my_profile(context):
    ...
```

The authenticated Django request should always be available.

---

## 2. DRF-Like Developer Experience

A Django developer should immediately understand how to use it.

Inspired by:

- Django REST Framework
- Django Admin
- Django URL routing
- Django app discovery

---

## 3. Authentication Should Be Automatic

If Django has authenticated a user, then: `request.user` should already work.

django-mcp should not implement its own authentication system.

Authentication remains the responsibility of Django and any configured authentication backends.

The framework should simply execute tools within the authenticated Django request lifecycle.

---

## Session Support

Since tools execute within the Django request lifecycle, they should automatically have access to: `request.session`

Example:

```python
from django_mcp import tool

@tool
def session_info(request):
    return {
        "session_key": request.session.session_key,
    }
```

No MCP-specific session management should be required.

---

## Design Goal

The following should work automatically:

```python
from django_mcp import tool

@tool
def my_profile(request):
    return {
        "username": request.user.username,
        "email": request.user.email,
    }
```

without requiring any MCP-specific authentication configuration.

django-mcp should consume Django's authentication system rather than extending or replacing it.

---

## 4. App-Based Discovery

Each Django app can define:

```text
members/
├── models.py
├── views.py
├── urls.py
├── mcp_tools.py
└── mcp_urls.py
```

The framework should automatically discover and register MCP tools.

---

# Project Structure

```text
django_mcp/
├── __init__.py
├── apps.py
├── registry.py
├── decorators.py
├── routing.py
├── discovery.py
├── schemas.py
├── serializers.py
├── permissions.py
├── authentication.py
├── exceptions.py
├── responses.py
├── views.py
├── urls.py
│
├── transports/
│   ├── __init__.py
│   ├── streamable_http.py
│   └── sse.py
│
├── tools/
│   ├── base.py
│   ├── function.py
│   └── class_based.py
│
├── protocol/
│   ├── jsonrpc.py
│   ├── requests.py
│   ├── responses.py
│   └── errors.py
│
└── management/
    └── commands/
        └── list_mcp_tools.py
```

---

# Developer Experience

## Minimal Configuration

### settings.py

```python
INSTALLED_APPS = [
    '...',
    "django_mcp",
    "members",
]
```

### urls.py

```python
from django.urls import path, include

urlpatterns = [
    path("mcp/",include("django_mcp.urls"))
]
```

Done.

---

# Tool Registration

## Function-Based Tools

### members/mcp_tools.py

```python
from django.conf import settings
from django.db import models

from django_mcp import tool


class Member(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    member_id = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)


@tool
def get_member_count(request):
    return {"count": Member.objects.count()}

```

---

## Named Tools

```python
from django_mcp import tool

@tool(
    name="member_lookup",
    description="Lookup member information"
)
def member_lookup(request, member_id: str):
    ...
```

---

# Application Routing

## Router Pattern

Inspired by DRF.

### members/mcp_urls.py

```python
from django_mcp import MCPRouter

router = MCPRouter()

router.register_tool("member_lookup")
router.register_tool("member_search")

urlpatterns = router.urls
```

---

# Automatic Discovery

During startup:

```python
from django.apps import AppConfig

AppConfig.ready()
```

framework scans:

```
members.mcp_tools
```

Similar to: `admin.py` auto-registration.

---

# Request Context

All tools receive the Django request.

```python
from django_mcp import tool

@tool
def get_profile(request):
    return {
        "username": request.user.username
    }
```

Available:

```
request.user
request.session
request.META
request.headers
request.tenant
request.organization
```

Any middleware-injected data should be available.

---

# Authentication

## Session Authentication

Works automatically: `request.user.is_authenticated`

No special MCP authentication layer.

---

## Token Authentication (Future)

Potential support:

```python
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

MCP_AUTHENTICATION_CLASSES = [
    SessionAuthentication,
    TokenAuthentication,
]
```

Modeled after DRF.

---

# Permission System

## IsAuthenticated

```python
from django_mcp import tool
from django_mcp.permissions import (
    IsAuthenticated
)

@tool(
    permissions=[IsAuthenticated]
)
def my_profile(request):
    return
```

---

## Django Permissions

```python
from django_mcp import tool
from django_mcp import DjangoPermission

@tool(
    permissions=[
        DjangoPermission(
            "members.view_member"
        )
    ]
)
def member_lookup(request):
    return
```

---

## Custom Permissions

```python
from django_mcp.permissions import MCPPermission

class IsManager(MCPPermission):

    def has_permission(self, request, tool ):
        return request.user.groups.filter(
            name="Managers"
        ).exists()
```

---

# Tool Metadata

## Rich Tool Definition

```python
from django_mcp import tool
from django_mcp.permissions import IsAuthenticated


@tool(
    name="member_lookup",
    description="Retrieve member demographic information",
    tags=["members"],
    permissions=[IsAuthenticated],
)
def member_lookup(request, member_id: str):
    return {"result": []}

```

Stored metadata:

```
{
    "name": "...",
    "description": "...",
    "input_schema": {...},
    "permissions": [...]
}
```

---

# Serializer System

Modeled heavily after DRF.

---

## Input Serializer

```python
from django_mcp import serializers


class MemberLookupSerializer(
    serializers.Serializer
):
    member_id = serializers.CharField()
```

Tool:

```python
from django_mcp import tool
from django_mcp import serializers

class MemberLookupSerializer(
    serializers.Serializer
):
    member_id = serializers.CharField()


@tool(
    input_serializer=MemberLookupSerializer
)
def member_lookup(request, validated_data):
    return {"result": []}
```

---

## Validation

Automatic:

```
{
    "member_id": "12345"
}
```

Invalid:

```
{
}
```

Returns:

```json
{
  "error": {
    "member_id": [
      "This field is required."
    ]
  }
}
```

---

# Schema Generation

MCP clients require schemas.

Generate automatically from serializers.

Example:

```python
from django_mcp import serializers

class MemberLookupSerializer(
    serializers.Serializer
):
    member_id = serializers.CharField()
```

Produces:

```json
{
  "type": "object",
  "properties": {
    "member_id": {
      "type": "string"
    }
  },
  "required": [
    "member_id"
  ]
}
```

---

# Class-Based Tools

## Base Class

```python
from django_mcp import MCPTool
from django_mcp.permissions import IsAuthenticated


class MemberLookupTool(MCPTool):

    description = "Member lookup"

    permission_classes = [
        IsAuthenticated
    ]

    def execute(self, request, member_id):
        return {"result": []}
```

---

## Async Version

```python
from django_mcp import MCPTool

class ItemSearchTool(MCPTool):

    async def execute(self, request, member_id):
        return {"result": []}
```

---

# Async Support

Function tools:

```python
from django_mcp import tool

@tool
async def search_items(request, member_id):
    return {"result": []} 
```

Class-based tools: `async def execute(...)`

Framework automatically detects async.

---

# MCP Context Object

In addition to request:

```python
from django_mcp import tool

@tool
def lookup(request, context):
    return {"result": []}
```

Context contains:

```
context.request
context.user
context.session
context.server
context.tool
```

Future-proof abstraction layer.

---

# Registry Design

## Global Registry

```
ToolRegistry
```

Responsibilities:

- Register tool
- Lookup tool
- Discover apps
- Build schemas
- Expose MCP tool list

Interface:

```
registry.register(tool)
registry.get(name)
registry.list()
```

---

# MCP Endpoints

## Streamable HTTP

Primary transport.

### GET

Tool discovery.

```http
GET /mcp/
```

---

### POST

RPC execution.

```http
POST /mcp/
```

Processes MCP JSON-RPC requests.

---

# SSE Support

Optional.

```text
/mcp/sse/
```

Used only for older clients.

Feature flag:

```python
MCP_ENABLE_SSE = True
```

---

# MCP Protocol Layer

## JSON-RPC

Support:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {}
}
```

---

# MCP Features by Phase

## Phase 1 (MVP)

### Must Have

- Tool decorator
- Registry
- App discovery
- Streamable HTTP transport
- Session authentication
- Permission classes
- Serializer validation
- Schema generation
- Function-based tools
- Async support

---

# Phase 2

### Nice To Have

- Class-based tools
- Tool grouping
- Tool tags
- Tool metadata
- Management commands

Example:

```bash
python manage.py list_mcp_tools
```

---

# Phase 3

### Protocol Expansion

Support:

- Resources
- Prompts
- Completions
- Sampling
- Roots

MCP-native capabilities.

---

# Use Cases

## Example: Member Lookup

```python
from django.conf import settings
from django.db import models
from django_mcp import tool, DjangoPermission


class Member(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    member_id = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)

    
@tool(
    permissions=[
        DjangoPermission(
            "members.view_member"
        )
    ]
)
def member_lookup(request, member_id):
    member = Member.objects.get(
        user=request.user,
        member_id=member_id
    )

    return {
        "member_id": member.member_id,
        "first_name": member.first_name,
        "last_name": member.last_name
    }
```

---

## Example: Current User

```python
from django_mcp import tool, IsAuthenticated

@tool(
    permissions=[
        IsAuthenticated
    ]
)
def current_user(request):

    return {
        "username": request.user.username,
        "email": request.user.email
    }
```

---

## Example: Store Search

```python
from django_mcp import tool, IsAuthenticated

@tool(
    permissions=[
        IsAuthenticated
    ]
)
def store_search(request, zip_code, radius):
    return {"result": []}
```

---

# Architectural Goal

Create the MCP equivalent of Django REST Framework.

The developer should be able to:

1. Install `django-mcp`
2. Add it to `INSTALLED_APPS`
3. Create `mcp_tools.py`
4. Decorate functions with `@tool`
5. Use existing Django auth, permissions, sessions, and ORM
6. Expose a standards-compliant MCP endpoint

without needing FastMCP, FastAPI, Starlette, separate processes, duplicated authentication, or a secondary application stack.

The framework should feel like a natural extension of Django rather than an MCP server embedded into Django.
