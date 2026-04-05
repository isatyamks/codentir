import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.config import settings


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class UnicodeSanitizingFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'msg'):
            if isinstance(record.msg, str):
                record.msg = record.msg.replace('\u202f', ' ')
                record.msg = record.msg.replace('\u00a0', ' ')
                record.msg = record.msg.replace('\u2013', '-')
                record.msg = record.msg.replace('\u2014', '--')
        
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, tuple):
                sanitized_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        arg = arg.replace('\u202f', ' ')
                        arg = arg.replace('\u00a0', ' ')
                        arg = arg.replace('\u2013', '-')
                        arg = arg.replace('\u2014', '--')
                    sanitized_args.append(arg)
                record.args = tuple(sanitized_args)
        
        return True


def setup_logger(
    name: str = "multimodal_rag",
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    level = log_level or settings.LOG_LEVEL.upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    try:
        import io
        if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        console_handler = logging.StreamHandler(sys.stdout)
    except (AttributeError, ValueError):
        try:
            import io
            console_handler = logging.StreamHandler(
                io.TextIOWrapper(
                    sys.stdout.buffer, 
                    encoding='utf-8', 
                    errors='backslashreplace',  # Show escape sequences for unencodable chars
                    line_buffering=True
                )
            )
        except (AttributeError, io.UnsupportedOperation):
            console_handler = logging.StreamHandler(sys.stdout)
    
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    console_handler.addFilter(UnicodeSanitizingFilter())
    
    console_format = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    log_path = settings.log_path / (log_file or settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    logger.propagate = False
    
    return logger


def get_logger(name: str = "multimodal_rag") -> logging.Logger:
    return logging.getLogger(name) if logging.getLogger(name).handlers else setup_logger(name)


logger = setup_logger()
