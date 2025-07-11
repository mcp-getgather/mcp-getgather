import importlib
import os
import pkgutil

# Dynamically import all modules in the package so that FastHTML app routes are registered.
package_path = os.path.dirname(__file__)
for finder, name, ispkg in pkgutil.iter_modules([package_path]):
    full_name = f"{__package__}.{name}"
    importlib.import_module(full_name)
