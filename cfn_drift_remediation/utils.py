import dataclasses
import json
from typing import Union, List, Mapping, Iterable, Optional

from jsonpointer import resolve_pointer

from .cli_exceptions import DriftTypeNotImplementedError


def get_desired_states(stack_resource_drifts: List) -> Iterable["DesiredState"]:
    for x in stack_resource_drifts:
        resource_type: str = x["ResourceType"]
        actual: Mapping = json.loads(x["ActualProperties"])
        expected: Mapping = json.loads(x["ExpectedProperties"])
        differences = [
            Difference(
                PropertyPath=d["PropertyPath"],
                # The ActualProperties and ExpectedProperties will have the right type
                # Inside the PropertyDifferences everything is a string
                ActualValue=resolve_pointer(actual, d["PropertyPath"], None),
                ExpectedValue=resolve_pointer(expected, d["PropertyPath"], None),
                DifferenceType=d["DifferenceType"],
            )
            for d in x["PropertyDifferences"]
        ]
        yield DesiredState(
            id=x["PhysicalResourceId"],
            type=resource_type,
            differences=differences,
        )


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
    ActualValue: Optional[Union[str, int, float, bool, dict, list]]
    ExpectedValue: Optional[Union[str, int, float, bool, dict, list]]
    DifferenceType: str
