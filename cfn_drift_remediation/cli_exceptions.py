from textwrap import dedent


class TestValueMismatchError(Exception):
    def __init__(self, state, patch, *args):
        super(TestValueMismatchError, self).__init__(*args)
        self.state = state
        self.patch = patch

    def error_message(self):
        return dedent(
            f"""
        The {self.state.type} {self.state.id} is not in the expected state.
        Possible things problems:
        - Drift detection is not up to date (solution: rerun drift deteciont)
        - Cloud Control might see a different order in a list (currently not supported)

        Patch document: {self.patch}
        """
        )


class DriftTypeNotImplementedError(NotImplementedError):
    pass


class CloudControlNotSupportedError(Exception):
    pass
