import logging

from src.modules.auth_tenants.application.ports import Mailer

logger = logging.getLogger("restauhub.mail")


class ConsoleMailer(Mailer):
    """Implémentation de développement : journalise au lieu d'envoyer un
    email réel. À remplacer par un adaptateur SMTP/API (ex. Postmark, SES)
    avant la mise en production — le port `Mailer` ne change pas."""

    async def send_invitation(self, *, to: str, tenant_name: str, activation_link: str) -> None:
        logger.info("[invitation] à %s pour rejoindre %s : %s", to, tenant_name, activation_link)

    async def send_password_reset(self, *, to: str, reset_link: str) -> None:
        logger.info("[password_reset] à %s : %s", to, reset_link)
