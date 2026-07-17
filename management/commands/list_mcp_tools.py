from django.core.management.base import BaseCommand

from django_mcp.registry import registry


class Command(BaseCommand):
    help = "List all registered MCP tools"

    def handle(self, *args, **options):
        tools = registry.list()

        if not tools:
            self.stdout.write(self.style.WARNING("No MCP tools registered."))
            return

        self.stdout.write(self.style.SUCCESS(f"Registered MCP tools ({len(tools)}):"))
        self.stdout.write("")

        for name, tool in tools.items():
            schema = tool.get_schema()
            permissions = [
                perm.__class__.__name__ if hasattr(perm, "__class__") else str(perm)
                for perm in tool.permission_classes
            ]

            self.stdout.write(f"  {name}")
            self.stdout.write(f"    Description: {tool.description or '(none)'}")
            self.stdout.write(f"    Tags: {', '.join(tool.tags) if tool.tags else '(none)'}")
            self.stdout.write(f"    Permissions: {', '.join(permissions) if permissions else '(none)'}")

            props = schema.get("properties", {})
            required = schema.get("required", [])
            if props:
                self.stdout.write("    Parameters:")
                for param_name, param_schema in props.items():
                    is_required = param_name in required
                    param_type = param_schema.get("type", "unknown")
                    self.stdout.write(f"      - {param_name} ({param_type}){' [required]' if is_required else ''}")

            self.stdout.write("")
