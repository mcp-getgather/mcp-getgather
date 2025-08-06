import importlib
import pkgutil


def auto_import(package_name: str):
    package = __import__(package_name, fromlist=["dummy"])
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package_name}.{module_name}")
