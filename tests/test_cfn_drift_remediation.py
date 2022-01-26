from os.path import dirname
from pathlib import Path

import toml

from cfn_drift_remediation import __version__
from cfn_drift_remediation import object_tools


def test_version():
    with open(Path(dirname(__file__)).parent / 'pyproject.toml', 'r') as fh:
        pyproject = toml.load(fh)
    assert __version__ == pyproject['tool']['poetry']['version']


def test_cast_from_schema():
    schema = {
        "properties": {
            "ShouldBeInteger": {"type": "integer"},
            "ShouldBeNumber": {"type": "number"},
            "ShouldBeString": {"type": "string"},
            "ShouldBeBoolean": {"type": "boolean"},
        }
    }

    cases = [
        # ({object}, {expected})
        (
            {
                'ShouldBeInteger': '1',
                'ShouldBeNumber': '0.2',
                'ShouldBeString': 3,
                'ShouldBeBoolean': 'Yes',
            },
            {
                'ShouldBeInteger': 1,
                'ShouldBeNumber': 0.2,
                'ShouldBeString': "3",
                'ShouldBeBoolean': True,
            }
        ),
        ({'ShouldBeString': 0.2}, {'ShouldBeString': "0.2"}),
        ({'ShouldBeString': False}, {'ShouldBeString': "False"}),
        ({'ShouldBeString': True}, {'ShouldBeString': "True"}),
        ({'ShouldBeBoolean': 'N'}, {'ShouldBeBoolean': False}),
        ({'ShouldBeBoolean': 0}, {'ShouldBeBoolean': False}),
        ({'ShouldBeBoolean': 1}, {'ShouldBeBoolean': True}),
    ]
    for obj, expected in cases:
        object_tools.fix_types(obj, schema)
        assert obj == expected
