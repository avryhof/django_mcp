from django.contrib import admin

from django_mcp.models import ClientCredential


@admin.register(ClientCredential)
class ClientCredentialAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "is_active", "created_at", "last_modified_at"]
    list_filter = ["user", "is_active",]
    search_fields = ["name", "user__username", "user__first_name", "user__last_name"]
    