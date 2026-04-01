import logging

from rich.console import Console
from rich.logging import RichHandler

_ROOT_LOGGER_NAME = "patan"
_CONFIGURED = False
_CONSOLE: Console | None = None


def get_console() -> Console:
    """返回共享的 rich console。"""
    global _CONSOLE
    if _CONSOLE is None:
        _CONSOLE = Console(stderr=True)
    return _CONSOLE


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """配置 patan 日志根节点，仅初始化一次。"""
    global _CONFIGURED

    root_logger = logging.getLogger(_ROOT_LOGGER_NAME)
    if not _CONFIGURED:
        handler = RichHandler(
            console=get_console(),
            rich_tracebacks=True,
            show_path=False,
            markup=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger.addHandler(handler)
        root_logger.propagate = False
        _CONFIGURED = True

    root_logger.setLevel(level)
    return root_logger


def get_logger(name: str | None = None) -> logging.Logger:
    """获取模块 logger。

    默认返回 `patan` 根 logger，传入 `__name__` 时会得到模块级 logger，
    并继承 patan 根 logger 的 handler/level 配置。
    """
    configure_logging()

    if not name or name == _ROOT_LOGGER_NAME:
        return logging.getLogger(_ROOT_LOGGER_NAME)

    logger = logging.getLogger(name)
    if not logger.name.startswith(f"{_ROOT_LOGGER_NAME}."):
        logger = logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
    return logger


logger = get_logger()
