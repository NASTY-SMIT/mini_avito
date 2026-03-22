from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'apps.accounts'
    verbose_name = "Аккаунты"

    def ready(self):
        import apps.accounts.signals  # noqa
