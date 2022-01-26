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
        Maybe you have to rerun drift detection, or the type of the values may be a mismatch.
        
        Patch document: {self.patch}
        """
        )


class DriftTypeNotImplementedError(NotImplementedError):
    pass
