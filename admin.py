from django.contrib import admin

from django_mcp.models import ClientCredential, MCPToolConfig


def _sync_tools_from_registry():
    """Sync registered tools to MCPToolConfig, preserving existing enable/disable state."""
    try:
        from .registry import registry

        registry.discover_apps()
        registered_names = set(registry.list().keys())

        existing = set(
            MCPToolConfig.objects.filter(name__in=registered_names).values_list("name", flat=True)
        )
        to_create = []
        for name in registered_names:
            if name not in existing:
                tool = registry.get(name)
                to_create.append(
                    MCPToolConfig(
                        name=name,
                        description=getattr(tool, "description", "") or "",
                        tags=", ".join(getattr(tool, "tags", []) or []),
                    )
                )
        if to_create:
            MCPToolConfig.objects.bulk_create(to_create, ignore_conflicts=True)
    except Exception:
        pass


@admin.register(MCPToolConfig)
class MCPToolConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "tags", "enabled"]
    list_filter = ["enabled", "tags"]
    search_fields = ["name", "description", "tags"]
    list_editable = ["enabled"]
    actions = ["enable_tools", "disable_tools", "sync_tools"]

    def changelist_view(self, request, extra_context=None):
        _sync_tools_from_registry()
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description="Enable selected tools")
    def enable_tools(self, request, queryset):
        count = queryset.update(enabled=True)
        self.message_user(request, f"Enabled {count} tool(s).")

    @admin.action(description="Disable selected tools")
    def disable_tools(self, request, queryset):
        count = queryset.update(enabled=False)
        self.message_user(request, f"Disabled {count} tool(s).")

    @admin.action(description="Sync tools from registry")
    def sync_tools(self, request, queryset):
        _sync_tools_from_registry()
        self.message_user(request, "Tools synced from registry.")


@admin.register(ClientCredential)
class ClientCredentialAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "is_active", "created_at",]
    list_filter = ["user", "is_active",]
    search_fields = ["name", "user__username", "user__first_name", "user__last_name"]
    