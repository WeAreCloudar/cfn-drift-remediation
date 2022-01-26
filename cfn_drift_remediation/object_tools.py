from copy import deepcopy
from distutils.util import strtobool
from typing import MutableMapping

from fastjsonschema import compile as compile_schema, JsonSchemaValueException
from jsonpointer import JsonPointer

MAX_FIXES = 50  # if there is an error in our error correction, we don't want to keep trying


def fix_types(partial_object: MutableMapping, cfn_schema: MutableMapping) -> None:
    """
    Fix potential type errors, using the provided schema to know the types.

    The provided (partial) object will be mutated

    We do our best to support partial objects, but assume the CloudFormation
    Resource Type Schema to do that. Other validation errors (like invalid values)
    will prevent this function from working
    """
    # We are going to edit the schema, so make a deep copy
    cfn_schema = deepcopy(cfn_schema)
    make_properties_optional(cfn_schema)
    validate = compile_schema(cfn_schema)

    for _ in range(MAX_FIXES):
        try:
            validate(partial_object)
            # Everything is valid, so we do not need to do any fixes
            break
        except JsonSchemaValueException as e:
            # There is at least one problem, try to fix it
            cast_type_from_exception(partial_object, e)

    # We could track if our fixes worked before we reached MAX_FIXES, but doing
    # an extra validation is easier
    validate(partial_object)


def cast_type_from_exception(o: MutableMapping, e: JsonSchemaValueException) -> None:
    """
    Read the given validation error, and try to cast the value in the object.

    If the validation error is not a type error, an AssertionError will be raised
    If we do not know how to cast this type (eg. it should be a dictionary), a
    NotImplementedError is raised
    """
    assert e.rule == "type", "failure should be based on the type"

    if e.rule_definition == "integer":
        new_value = int(e.value)
    elif e.rule_definition == "number":
        new_value = float(e.value)
    elif e.rule_definition == "string":
        new_value = str(e.value)
    elif e.rule_definition == "boolean":
        if isinstance(e.value, str):
            new_value = strtobool(e.value.lower())
        elif isinstance(e.value, int):
            new_value = bool(e.value)
        else:
            raise NotImplementedError(f"We don't know how to cast {e.value} to a boolean")
    else:
        # Other types in jsonschema are object, array, and null
        # https://json-schema.org/understanding-json-schema/reference/type.html
        raise NotImplementedError(f"We don't know how to cast {e.rule_definition} yet")

    # path starts always with "data", we don't want that in the pointer
    pointer = JsonPointer.from_parts(e.path[1:])
    assert pointer.resolve(o) == e.value, "The original value and the value in the exception do not match"
    pointer.set(o, new_value)


def make_properties_optional(cfn_schema: MutableMapping) -> None:
    """
    Make all properties optional by removing the "required" key from the schema

    One reason to use this function, is if you want to validate a partial object
    against the schema, in that case you do not want an enforcement of the
    required properties.
    """

    cfn_schema.pop("required", None)
    # CloudFormation resource schema uses references and the "definitions" key
    # for nesting, so we also want to remove the required properties there.
    # Solving this in a generic way is probably harder
    for name, definition in cfn_schema.get("definitions", {}).items():
        definition.pop("required", None)
