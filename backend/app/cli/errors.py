class CliError(Exception):
    def __init__(self, message: str, exit_code: int = 2, *, details=None):
        super().__init__(message)
        self.exit_code = exit_code
        self.details = details
