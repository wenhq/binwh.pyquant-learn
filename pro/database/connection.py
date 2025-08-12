from contextlib import contextmanager
import threading

import pymysql
from pymysql.cursors import DictCursor

from util.logger import get_logger

class MySQLConnectionManager:
   
    """MySQL数据库连接管理器"""
    
    def __init__(self, host: str = 'localhost', port: int = 3306, 
                 user: str = 'root', password: str = '', database: str = '',
                 charset: str = 'utf8mb4', **kwargs):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': charset,
            'autocommit': False,
            'cursorclass': DictCursor,  # 默认使用字典游标
            **kwargs
        }
        self.logger = get_logger("proj.database")
        self._local = threading.local()
    
    @contextmanager
    def get_connection(self):
        """上下文管理器获取数据库连接"""
        conn = None
        try:
            conn = pymysql.connect(**self.config)
            self.logger.debug(f"MySQL连接已建立: {self.config['host']}:{self.config['port']}")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"MySQL操作失败: {e}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()
                self.logger.debug("MySQL连接已关闭")
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False
