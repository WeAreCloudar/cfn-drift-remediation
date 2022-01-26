import dataclasses
import json
from typing import Union, List, Mapping, Iterable

from jsonpointer import set_pointer, resolve_pointer

from .cli_exceptions import DriftTypeNotImplementedError
from .object_tools import fix_types
from .schema_tools import CFN_SCHEMA_FOLDER


def get_desired_states(stack_resource_drifts: List) -> Iterable["DesiredState"]:
    for x in stack_resource_drifts:
        resource_type = x["ResourceType"]
        differences = [Difference(**d) for d in x["PropertyDifferences"]]
        fix_type_of_values_in_differences(differences, resource_type)
        yield DesiredState(
            id=x["PhysicalResourceId"],
            type=resource_type,
            differences=differences,
        )


def fix_type_of_values_in_differences(differences: List["Difference"], resource_type: str) -> None:
    actual_model = {}
    expected_model = {}

    for diff in differences:
        set_pointer(actual_model, diff.PropertyPath, diff.ActualValue)
        set_pointer(expected_model, diff.PropertyPath, diff.ExpectedValue)

    with open(CFN_SCHEMA_FOLDER / f"{resource_type.replace('::', '-').lower()}.json", "r") as fh:
        schema = json.load(fh)
    fix_types(actual_model, schema)
    fix_types(expected_model, schema)

    for diff in differences:
        diff.ActualValue = resolve_pointer(actual_model, diff.PropertyPath)
        diff.ExpectedValue = resolve_pointer(expected_model, diff.PropertyPath)


def create_patch(differences: List["Difference"]) -> List[Mapping]:
    ops = []
    for diff in differences:
        if diff.DifferenceType != "NOT_EQUAL":
            raise DriftTypeNotImplementedError("only NOT_EQUAL drift is currently supported")
        ops.extend(
            [
                {
                    "op": "test",
                    "path": diff.PropertyPath,
                    "value": diff.ActualValue,
                },
                {
                    "op": "replace",
                    "path": diff.PropertyPath,
                    "value": diff.ExpectedValue,
                },
            ]
        )
    return ops


@dataclasses.dataclass
class DesiredState:
    id: str
    type: str
    differences: list["Difference"]


@dataclasses.dataclass
class Difference:
    # We use the Boto3 names, so CamelCase
    PropertyPath: str
    ActualValue: Union[str, int, float, bool]
    ExpectedValue: Union[str, int, float, bool]
    DifferenceType: str
