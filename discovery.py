import importlib
import logging

from django.apps import apps

logger = logging.getLogger("django_mcp")


def discover_mcp_tools():
    from .registry import registry

    registry.discover_apps()
    return registry.list()


def discover_app_tools(app_label):
    module_name = f"{app_label}.mcp_tools"
    try:
        module = importlib.import_module(module_name)
        logger.debug("Discovered MCP tools in: %s", module_name)
        return True
    except ImportError:
        logger.debug("No mcp_tools module found in: %s", app_label)
        return False
