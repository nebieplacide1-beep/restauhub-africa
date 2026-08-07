from src.shared_kernel.exceptions import ConflictError, NotFoundError, ValidationError


class SuccursaleNotFoundError(NotFoundError):
    code = "succursale_not_found"


class InvalidOpeningHoursError(ValidationError):
    code = "invalid_opening_hours"


class StaffAssignmentAlreadyExistsError(ConflictError):
    code = "staff_assignment_already_exists"
