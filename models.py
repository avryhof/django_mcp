import hashlib
import secrets
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class ClientCredential(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mcp_credentials")
    name = models.CharField(max_length=255, help_text="Descriptive name, e.g. 'Claude Desktop'")
    client_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    client_secret_hash = models.CharField(max_length=128, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

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
