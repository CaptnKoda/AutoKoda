"""Addon-wide logging to stderr. Every module logs through
logging.getLogger(__name__), whose name sits under this package, so the
one handler attached here catches everything."""

import functools
import logging
import sys

# Set to logging.DEBUG to also see routine skips (per-socket, per-material)
LOG_LEVEL = logging.INFO

_LOG_FORMAT = "[Auto Koda] %(levelname)s %(module)s.%(funcName)s:%(lineno)d: %(message)s"

log = logging.getLogger(__name__)


def setup_logging():
    """Attaches the stderr handler. Safe to call again (e.g. on addon reload)."""
    shutdown_logging()

    logger = logging.getLogger(__package__)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logger.addHandler(handler)


def shutdown_logging():
    logger = logging.getLogger(__package__)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def _describe_context(context):
    """One-line snapshot of what an operator was working on."""
    try:
        active = context.active_object.name if context.active_object else None
        selected = [obj.name for obj in context.selected_objects]
        return f"mode={context.mode}, active={active!r}, selected={selected}"
    except Exception as e:
        return f"context unavailable ({type(e).__name__}: {e})"
# Example: _describe_context(context) -> "mode=OBJECT, active='Body', selected=['Body', 'Head']"


class LoggedOperator:
    """Operator mixin adding log_report(): report() plus a log entry.

    This can't simply override report(): on a registered operator Blender
    finds its own RNA methods before any Python class attribute, so the
    override would never run."""

    def log_report(self, type, message):
        if 'ERROR' in type:
            level = logging.ERROR
        elif 'WARNING' in type:
            level = logging.WARNING
        else:
            level = logging.INFO
        log.log(level, f"{self.bl_idname}: {message}", stacklevel=2)
        self.report(type, message)


def logged_execute(execute):
    """Decorator for Operator.execute(): turns any uncaught exception into
    a logged traceback plus an error report.

    The wrapper's signature must stay exactly (self, context) -- Blender
    checks the argument count when registering the class, so *args fails."""
    @functools.wraps(execute)
    def wrapper(self, context):
        log.debug(f"{self.bl_idname}: started ({_describe_context(context)})")
        try:
            return execute(self, context)
        except Exception as e:
            log.exception(f"{self.bl_idname}: crashed ({_describe_context(context)})")
            self.log_report({'ERROR'}, f"{self.bl_label} failed: {type(e).__name__}: {e} - see console")
            return {'CANCELLED'}
    return wrapper
