import importlib
import logging

from django.apps import apps

from .exceptions import ToolAlreadyRegistered, ToolNotFound

logger = logging.getLogger("django_mcp")


class ToolRegistry:

    def __init__(self):
        self._tools = {}

    def register(self, tool_func, name=None, description=None, input_serializer=None, permissions=None, tags=None):
        tool_name = name or getattr(tool_func, "__name__", str(tool_func))

        if tool_name in self._tools:
            raise ToolAlreadyRegistered(f"Tool '{tool_name}' is already registered.")

        from .tools.function import FunctionTool

        tool = FunctionTool(
            func=tool_func,
            name=tool_name,
            description=description or getattr(tool_func, "__doc__", "") or "",
            input_serializer=input_serializer,
            permissions=permissions or [],
            tags=tags or [],
        )

        self._tools[tool_name] = tool
        logger.debug("Registered MCP tool: %s", tool_name)
        return tool

    def get(self, name):
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFound(f"Tool '{name}' not found.")
        return tool

    def list(self):
        return dict(self._tools)

    def list_tools(self):
        return list(self._tools.values())

    def clear(self):
        self._tools.clear()

    def discover_apps(self):
        for app_config in apps.get_app_configs():
            self._discover_app(app_config)

    def _discover_app(self, app_config):
        module_name = f"{app_config.name}.mcp_tools"
        try:
            module = importlib.import_module(module_name)
            logger.debug("Discovered MCP tools in: %s", module_name)
        except ImportError:
            pass


registry = ToolRegistry()
