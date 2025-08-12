import os
import logging
import logging.config
import yaml
from pathlib import Path
from typing import Optional


class LoggerManager:
    """全局日志管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not LoggerManager._initialized:
            self.config_path = None
            self.config = None
            LoggerManager._initialized = True
    
    def load_config(self, config_path: Optional[str] = None):
        """加载日志配置文件"""
        if config_path is None:
            # 自动查找配置文件
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / "config" / "logging_config.yaml"
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")
        
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 创建日志目录
        if 'custom' in self.config and 'log_dir' in self.config['custom']:
            log_dir = Path(self.config['custom']['log_dir'])
            log_dir.mkdir(exist_ok=True)
        
        # 应用配置
        logging.config.dictConfig(self.config)
        self.config_path = config_path
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """获取logger实例"""
        if self.config is None:
            self.load_config()
        
        if name is None:
            name = "proj"
        
        return logging.getLogger(name)
    
    def set_level(self, level: str, logger_name: str = "proj"):
        """动态设置日志级别"""
        logger = logging.getLogger(logger_name)
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        if level.upper() in level_map:
            logger.setLevel(level_map[level.upper()])
    
    def reload_config(self):
        """重新加载配置"""
        if self.config_path:
            self.load_config(self.config_path)


# 全局实例
logger_manager = LoggerManager()


def get_logger(name: str = None) -> logging.Logger:
    """获取logger的便捷函数"""
    return logger_manager.get_logger(name)


def setup_logging(config_path: str = None):
    """初始化日志系统的便捷函数"""
    logger_manager.load_config(config_path)


# 为了向后兼容，提供一些常用的logger实例
def get_main_logger() -> logging.Logger:
    """获取主应用logger"""
    return get_logger("proj")


def get_data_logger() -> logging.Logger:
    """获取数据处理logger"""
    return get_logger("proj.data")


def get_model_logger() -> logging.Logger:
    """获取模型训练logger"""
    return get_logger("proj.model")


# 装饰器：为函数添加日志
def log_function_call(logger_name: str = "proj"):
    """装饰器：记录函数调用"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            logger.info(f"调用函数: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator


# Jupyter Notebook 专用函数
def setup_notebook_logging(level: str = "INFO"):
    """为Jupyter Notebook设置日志"""
    # 确保日志管理器已初始化
    logger_manager.load_config()
    
    # 获取根logger并设置级别
    root_logger = logging.getLogger()
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    if level.upper() in level_map:
        root_logger.setLevel(level_map[level.upper()])
    
    return get_logger("proj")
