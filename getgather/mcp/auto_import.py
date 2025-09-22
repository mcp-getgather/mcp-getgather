import importlib
import inspect
import pkgutil
import sys
from typing import Any

from getgather.mcp.registry import BrandMCPBase, GatherMCP


def has_mcp_class(module: Any) -> bool:
    """Check if a module contains a class that inherits from BrandMCPBase or GatherMCP."""
    for _, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and (issubclass(obj, BrandMCPBase) or issubclass(obj, GatherMCP)):
            # Exclude the base classes themselves
            if obj is not BrandMCPBase and obj is not GatherMCP:
                return True
    return False


def auto_import(package_name: str):
    package = __import__(package_name, fromlist=["dummy"])
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        full_module_name = f"{package_name}.{module_name}"
        module = importlib.import_module(full_module_name)

        # Remove non-MCP modules
        if not has_mcp_class(module) and full_module_name in sys.modules:
            del sys.modules[full_module_name]
