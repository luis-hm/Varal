from django.apps import AppConfig


class Config(AppConfig):
    name = "apps.pagamentos"

    def ready(self):
        from . import signals  # noqa: F401
