import logging
import sys
import os
from pathlib import Path

def get_logger(
    name: str = "data_generation",
    log_file: str = "app.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    创建一个简单的 logger：控制台 + 单个日志文件（不轮转）

    Args:
        name: logger 名称
        log_file: 日志文件名（默认 app.log）
        level: 日志级别

    Returns:
        logging.Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # 防止日志重复
    if logger.handlers:
        return logger
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    log_dir = "./logs"

    file_handler = logging.FileHandler(os.path.join(log_dir, log_file), encoding="utf-8")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
