"""Custom exceptions for Layer 2 constraint optimization."""


class InfeasibleError(Exception):
    """Raised when the MILP has no feasible solution."""

    def __init__(self, message: str, binding_constraint: str | None = None):
        self.binding_constraint = binding_constraint
        super().__init__(message)
