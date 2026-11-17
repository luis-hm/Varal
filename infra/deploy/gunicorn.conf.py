"""Avoid logging request-derived text and exception tracebacks in deployed environments."""
import logging

from gunicorn.glogging import Logger


class SafeFormatter(logging.Formatter):
    def format(self, record):
        # Ignore interpolated arguments and exc_info, which may contain request URLs.
        return f"gunicorn event level={record.levelname}"


class SafeLogger(Logger):
    def setup(self, cfg):
        super().setup(cfg)
        for logger in (self.error_log, self.access_log):
            logger.propagate = False
            for handler in logger.handlers:
                handler.setFormatter(SafeFormatter())


logger_class = SafeLogger
accesslog = None
errorlog = "-"
loglevel = "warning"
capture_output = False
