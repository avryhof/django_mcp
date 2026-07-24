import hashlib
import secrets
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class MCPToolConfig(models.Model):
    """Tracks registered MCP tools and allows enabling/disabling them via admin."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    tags = models.CharField(max_length=500, blank=True, default="")
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "MCP Tool"
        verbose_name_plural = "MCP Tools"

    def __str__(self):
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} ({status})"


class ClientCredential(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mcp_credentials")
    name = models.CharField(max_length=255, help_text="Descriptive name, e.g. 'Claude Desktop'")
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    client_secret_hash = models.CharField(max_length=128, editable=False)
    is_active = models.BooleanField(default=True)
    global_access = models.BooleanField(
        default=False,
        help_text="Allow this credential to access all users' objects. Only available for superuser credentials."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.global_access and not self.user.is_superuser:
            from django.core.exceptions import ValidationError
            raise ValidationError({"global_access": "Global access is only available for superuser accounts."})

    def __str__(self):
        return f"{self.name} ({self.client_id})"

    @staticmethod
    def _hash_secret(secret):
        return hashlib.sha256(secret.encode()).hexdigest()

    def set_secret(self, raw_secret):
        self.client_secret_hash = self._hash_secret(raw_secret)

    def verify_secret(self, raw_secret):
        return secrets.compare_digest(self.client_secret_hash, self._hash_secret(raw_secret))

    @staticmethod
    def generate_secret():
        return secrets.token_hex(24)
