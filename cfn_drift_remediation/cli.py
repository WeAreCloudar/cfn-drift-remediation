#!/usr/bin/env python
import json
import sys
from argparse import ArgumentParser
from typing import Iterable

import boto3

from .aws_error_utils import errors
from .cli_exceptions import TestValueMismatchError, DriftTypeNotImplementedError, CloudControlNotSupportedError
from .utils import DesiredState, get_desired_states, create_patch


def run():
    parser = ArgumentParser()
    parser.add_argument(
        "stack",
        help="CloudFormation Stack that has (detected) drift",
    )

    args = parser.parse_args()
    # Use the default session
    session = boto3.Session()

    skipped = False
    for state in get_desired_state(session, args.stack):
        try:
            print(f"{state.type} {state.id}: updating")
            set_state(session, state)
            print(f"{state.type} {state.id}: updated")
        except CloudControlNotSupportedError as e:
            print(f"{state.type} {state.id}: SKIPPING (not supported in Cloud Control API)")
            skipped = True
            continue
        except TestValueMismatchError as e:
            print(e.error_message(), file=sys.stderr)
            print("ABORTED: all drift might not be remediated", file=sys.stderr)
            exit(1)
        except DriftTypeNotImplementedError as e:
            print(e, file=sys.stderr)
            print("ABORTED: all drift might not be remediated", file=sys.stderr)
            exit(1)
    if skipped:
        print("WARNING: some resources were skipped", file=sys.stderr)
        exit(2)


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
    except cc.exceptions.UnsupportedActionException as e:
        raise CloudControlNotSupportedError(f"{state.type} is not supported yet by AWS") from e
    except errors.ValidationException as e:
        if e.message == "[TEST Operation] value mismatch":
            raise TestValueMismatchError(state=state, patch=patch) from e
        raise

    cc.get_waiter("resource_request_success").wait(RequestToken=request_token)


if __name__ == "__main__":
    run()
