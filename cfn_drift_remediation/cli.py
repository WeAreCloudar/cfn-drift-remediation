#!/usr/bin/env python
import json
import sys
from argparse import ArgumentParser
from typing import Iterable

import boto3

from .aws_error_utils import errors
from .cli_exceptions import TestValueMismatchError, DriftTypeNotImplementedError
from .schema_tools import get_schemas
from .utils import DesiredState, get_desired_states, create_patch


def run():
    parser = ArgumentParser()
    parser.add_argument(
        "stack",
        help="CloudFormation Stack that has (detected) drift",
    )
    parser.add_argument('--update-schemas', action='store_true')

    args = parser.parse_args()
    # Use the default session
    session = boto3.Session()

    # Download the latest schemas
    get_schemas(force_update=args.update_schemas, region=session.region_name)

    for state in get_desired_state(session, args.stack):
        try:
            print(f"{state.type} {state.id}: updating")
            set_state(session, state)
            print(f"{state.type} {state.id}: updated")
        except TestValueMismatchError as e:
            print(e.error_message(), file=sys.stderr)
            print("ABORTED: all drift might not be remediated", file=sys.stderr)
            exit(1)
        except DriftTypeNotImplementedError as e:
            print(e, file=sys.stderr)
            print("ABORTED: all drift might not be remediated", file=sys.stderr)
            exit(1)


def get_desired_state(session: boto3.Session, stack: str) -> Iterable[DesiredState]:
    cfn = session.client("cloudformation")

    response = cfn.describe_stack_resource_drifts(
        StackName=stack,
        StackResourceDriftStatusFilters=["MODIFIED"],
    )
    next_token = response.get("NextToken", False)
    yield from get_desired_states(response["StackResourceDrifts"])
    while next_token:
        response = cfn.describe_stack_resource_drifts(
            StackName=stack,
            StackResourceDriftStatusFilters=["MODIFIED"],
            NextToken=next_token,
        )
        next_token = response.get("NextToken", False)
        yield from get_desired_states(response["StackResourceDrifts"])


def set_state(session: boto3.Session, state: "DesiredState") -> None:
    cc = session.client("cloudcontrol")
    patch = json.dumps(create_patch(state.differences))
    try:
        request_token = cc.update_resource(TypeName=state.type, Identifier=state.id, PatchDocument=patch,)[
            "ProgressEvent"
        ]["RequestToken"]
    except errors.ValidationException as e:
        if e.message == "[TEST Operation] value mismatch":
            raise TestValueMismatchError(state=state, patch=patch) from e
        raise

    cc.get_waiter("resource_request_success").wait(RequestToken=request_token)


if __name__ == "__main__":
    run()
