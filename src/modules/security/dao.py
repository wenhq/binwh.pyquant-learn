from typing import Dict, List, Any, Optional, Union, Tuple

from database.base import BaseTable

class SecuTable(BaseTable):
    """用户表操作类"""
    
    @property
    def table_name(self) -> str:
        return "secutiry"
    
    @property
    def create_table_sql(self) -> str:
        return """
            SHOW TABLES LIKE 'security2'
        """

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名查找用户"""
        return self.find_one_where({'username': username})
    
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱查找用户"""
        return self.find_one_where({'email': email})
    
    def find_active_users(self) -> List[Dict[str, Any]]:
        """查找活跃用户"""
        return self.find_where({'is_active': 1}, order_by='created_at DESC')
