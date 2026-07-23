import logging

from django.apps import AppConfig

logger = logging.getLogger("django_mcp")


class DjangoMCPConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_mcp"
    verbose_name = "Django MCP"
    default = True

    def ready(self):
        super().ready()
        from .registry import registry

        registry.discover_apps()
        self._sync_tool_configs(registry)

    def _sync_tool_configs(self, registry):
        """Sync registered tools to MCPToolConfig, preserving existing enable/disable state."""
        from django.db import connection

        try:
            from .models import MCPToolConfig

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
                logger.info("Created %d new MCPToolConfig records", len(to_create))
        except Exception as exc:
            logger.debug("Could not sync MCPToolConfig (table may not exist yet): %s", exc)
