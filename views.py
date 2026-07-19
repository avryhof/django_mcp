import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

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


class MCPClientCredentialsView(View):
    template_name = "mcp/manage_credentials.html"

    def _get_mcp_endpoint(self, request):
        return request.build_absolute_uri("/mcp/")

    def get(self, request, *args, **kwargs):
        credentials = request.user.mcp_credentials.all()
        return render(request, self.template_name, {
            "credentials": credentials,
            "mcp_endpoint": self._get_mcp_endpoint(request),
        })

    def post(self, request, *args, **kwargs):
        from .models import ClientCredential

        action = request.POST.get("action")

        if action == "create":
            name = request.POST.get("name", "").strip()
            if not name:
                return render(request, self.template_name, {
                    "credentials": request.user.mcp_credentials.all(),
                    "error": "A name is required.",
                    "mcp_endpoint": self._get_mcp_endpoint(request),
                })

            secret = ClientCredential.generate_secret()
            credential = ClientCredential(user=request.user, name=name)
            credential.set_secret(secret)
            credential.save()

            credentials = request.user.mcp_credentials.all()
            return render(request, self.template_name, {
                "credentials": credentials,
                "new_credential": {
                    "client_id": str(credential.client_id),
                    "client_secret": secret,
                    "name": credential.name,
                },
                "mcp_endpoint": self._get_mcp_endpoint(request),
            })

        elif action == "toggle":
            cred_id = request.POST.get("credential_id")
            try:
                credential = ClientCredential.objects.get(id=cred_id, user=request.user)
                credential.is_active = not credential.is_active
                credential.save(update_fields=["is_active"])
            except ClientCredential.DoesNotExist:
                pass

        elif action == "delete":
            cred_id = request.POST.get("credential_id")
            try:
                credential = ClientCredential.objects.get(id=cred_id, user=request.user)
                credential.delete()
            except ClientCredential.DoesNotExist:
                pass

        return redirect("mcp-credentials")

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
