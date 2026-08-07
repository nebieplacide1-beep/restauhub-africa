from src.shared_kernel.exceptions import (
    AccountLockedError,
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthenticatedError,
    ValidationError,
)


class TenantNotFoundError(NotFoundError):
    code = "tenant_not_found"


class TenantSuspendedError(ForbiddenError):
    code = "tenant_suspended"


class UserNotFoundError(NotFoundError):
    code = "user_not_found"


class InvalidCredentialsError(UnauthenticatedError):
    code = "invalid_credentials"


class InvalidTwoFactorCodeError(UnauthenticatedError):
    code = "invalid_code"


class TwoFactorAlreadyEnabledError(ConflictError):
    code = "two_factor_already_enabled"


class ChallengeExpiredError(UnauthenticatedError):
    code = "challenge_expired"


class InvalidOrRevokedTokenError(UnauthenticatedError):
    code = "invalid_or_revoked_token"


class AccountLockedDomainError(AccountLockedError):
    code = "account_locked"


class IdentifierAlreadyUsedError(ConflictError):
    code = "identifier_already_used"


class InvalidIdentifierFormatError(ValidationError):
    code = "invalid_identifier_format"


class InvitationNotFoundError(NotFoundError):
    code = "invitation_not_found"


class InvitationExpiredError(DomainError):
    code = "invitation_expired"
    http_status = 410


class PasswordResetTokenInvalidError(UnauthenticatedError):
    code = "invalid_or_expired_reset_token"
