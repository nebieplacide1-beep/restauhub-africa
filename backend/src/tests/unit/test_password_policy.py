import pytest

from src.modules.auth_tenants.domain.services import PasswordPolicy
from src.shared_kernel.exceptions import ValidationError


@pytest.mark.parametrize(
    "password",
    [
        "short1!",  # trop court
        "nouppercase1!",  # pas de majuscule
        "NoDigitsHere!",  # pas de chiffre
        "NoSymbolHere1",  # pas de symbole
    ],
)
def test_rejects_noncompliant_passwords(password: str) -> None:
    with pytest.raises(ValidationError):
        PasswordPolicy.validate(password)


def test_accepts_compliant_password() -> None:
    PasswordPolicy.validate("Str0ng!Passw0rd")  # ne doit pas lever
