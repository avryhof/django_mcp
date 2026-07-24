import logging
from datetime import timezone as tz

from django.utils import timezone

logger = logging.getLogger("django_mcp")


class MCPAuthentication:

    def authenticate(self, request):
        return None

    def __call__(self, request):
        return self.authenticate(request)


class SessionAuthentication(MCPAuthentication):

    def authenticate(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None


class RemoteUserAuthentication(MCPAuthentication):

    header = "REMOTE_USER"

    def authenticate(self, request):
        remote_user = request.META.get(self.header)
        if remote_user:
            return remote_user
        return None


class ClientCredentialsAuthentication(MCPAuthentication):

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:].strip()
        if ":" not in token:
            return None

        client_id_str, raw_secret = token.split(":", 1)

        try:
            import uuid as uuid_mod

            client_id = uuid_mod.UUID(client_id_str)
        except (ValueError, AttributeError):
            return None

        from .models import ClientCredential

        try:
            credential = ClientCredential.objects.select_related("user").get(
                client_id=client_id,
                is_active=True,
            )
        except ClientCredential.DoesNotExist:
            return None

        if not credential.verify_secret(raw_secret):
            logger.warning("Invalid client_secret for client_id %s", client_id_str)
            return None

        credential.last_used_at = timezone.now()
        credential.save(update_fields=["last_used_at"])

        request.mcp_global_access = credential.global_access
        return credential.user
