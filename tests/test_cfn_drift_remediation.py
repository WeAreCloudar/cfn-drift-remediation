from os.path import dirname
from pathlib import Path

import toml

from cfn_drift_remediation import __version__


def test_version():
    with open(Path(dirname(__file__)).parent / 'pyproject.toml', 'r') as fh:
        pyproject = toml.load(fh)
    assert __version__ == pyproject['tool']['poetry']['version']
