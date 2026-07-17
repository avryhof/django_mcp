from django.apps import AppConfig

from .registry import registry


class DjangoMCPConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_mcp"
    verbose_name = "Django MCP"
    default = True

    def ready(self):
        super().ready()
        registry.discover_apps()
