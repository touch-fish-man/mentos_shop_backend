import yaml
from loguru import logger
from logging import Handler, LogRecord
import os

class LoguruHandler(Handler):
    """
    自定义 Handler 将标准 logging 模块的日志转发到 loguru。
    """
    def emit(self, record: LogRecord) -> None:
        try:
            # 获取由 logging 格式化的日志消息
            message = self.format(record)
            # 将消息转发给 loguru
            logger_opt = logger.opt(depth=6, exception=record.exc_info)
            logger_opt.log(record.levelname, message)
        except Exception:
            self.handleError(record)


def load_loguru_config(yaml_path):
    """
    Load loguru configuration from a YAML file.
    """
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    # 清除 loguru 默认的日志处理器
    logger.remove()

    # 使用 YAML 配置中的处理器
    for handler in config['handlers']:
        logger.add(**handler)
