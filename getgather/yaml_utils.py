import re
from pathlib import Path
from typing import Any, cast

import yaml


class RegexLoader(yaml.SafeLoader):
    pass


def _construct_regex(loader: yaml.SafeLoader, node: yaml.nodes.ScalarNode) -> re.Pattern[str]:
    pattern = loader.construct_scalar(node)
    return re.compile(cast(re.Pattern[str], pattern))


RegexLoader.add_constructor("!regex", _construct_regex)


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r") as f:
        return yaml.load(f, Loader=RegexLoader)
