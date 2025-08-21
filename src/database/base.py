# util/database/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple

import pandas as pd

from util.logger import get_logger

from database.connection import MySQLConnectionManager

class BaseTable(ABC):
    """MySQL数据库表操作基类"""
    
    def __init__(self, db_manager: MySQLConnectionManager):
        self.db_manager = db_manager
        self.logger = get_logger(f"proj.database.{self.table_name}")
        self._ensure_table_exists()
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """表名，子类必须实现"""
        pass
    
    @property
    @abstractmethod
    def create_table_sql(self) -> str:
        """建表SQL，子类必须实现"""
        pass
    
    @property
    def columns(self) -> List[str]:
        """获取表的列名"""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"DESCRIBE {self.table_name}")
                return [row['Field'] for row in cursor.fetchall()]
    
    def _ensure_table_exists(self):
        """确保表存在，不存在则创建"""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(self.create_table_sql)
                    conn.commit()
                    self.logger.debug(f"表 {self.table_name} 检查/创建完成")
        except Exception as e:
            self.logger.error(f"创建表 {self.table_name} 失败: {e}")
            raise
    
    def insert_one(self, data: Dict[str, Any]) -> int:
        """插入单条记录"""
        columns = ', '.join([f"`{k}`" for k in data.keys()])
        placeholders = ', '.join(['%s' for _ in data])
        sql = f"INSERT INTO `{self.table_name}` ({columns}) VALUES ({placeholders})"
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, list(data.values()))
                conn.commit()
                row_id = cursor.lastrowid
                self.logger.debug(f"插入记录到 {self.table_name}，ID: {row_id}")
                return row_id
    
    def insert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """批量插入记录"""
        if not data_list:
            return 0
        
        columns = ', '.join([f"`{k}`" for k in data_list[0].keys()])
        placeholders = ', '.join(['%s' for _ in data_list[0]])
        sql = f"INSERT INTO `{self.table_name}` ({columns}) VALUES ({placeholders})"
        
        values_list = [list(data.values()) for data in data_list]
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                count = cursor.executemany(sql, values_list)
                conn.commit()
                self.logger.info(f"批量插入 {count} 条记录到 {self.table_name}")
                return count
    
    def upsert_one(self, data: Dict[str, Any], unique_keys: List[str] = None) -> int:
        """插入或更新单条记录 (ON DUPLICATE KEY UPDATE)"""
        columns = ', '.join([f"`{k}`" for k in data.keys()])
        placeholders = ', '.join(['%s' for _ in data])
        
        # 构建更新子句
        update_clause = ', '.join([f"`{k}` = VALUES(`{k}`)" for k in data.keys() 
                                  if unique_keys is None or k not in unique_keys])
        
        sql = f"""INSERT INTO `{self.table_name}` ({columns}) VALUES ({placeholders})
                  ON DUPLICATE KEY UPDATE {update_clause}"""
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, list(data.values()))
                conn.commit()
                row_id = cursor.lastrowid
                self.logger.debug(f"Upsert记录到 {self.table_name}，ID: {row_id}")
                return row_id
    
    def update_by_id(self, record_id: int, data: Dict[str, Any]) -> bool:
        """根据ID更新记录"""
        if not data:
            return False
        
        set_clause = ', '.join([f"`{k}` = %s" for k in data.keys()])
        sql = f"UPDATE `{self.table_name}` SET {set_clause} WHERE id = %s"
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, list(data.values()) + [record_id])
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self.logger.debug(f"更新 {self.table_name} 记录，ID: {record_id}")
                else:
                    self.logger.warning(f"未找到要更新的记录，ID: {record_id}")
                return success
    
    def update_where(self, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
        """根据条件更新记录"""
        if not data or not conditions:
            return 0
        
        set_clause = ', '.join([f"`{k}` = %s" for k in data.keys()])
        where_clause = ' AND '.join([f"`{k}` = %s" for k in conditions.keys()])
        sql = f"UPDATE `{self.table_name}` SET {set_clause} WHERE {where_clause}"
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, list(data.values()) + list(conditions.values()))
                conn.commit()
                count = cursor.rowcount
                self.logger.info(f"更新 {count} 条记录在 {self.table_name}")
                return count
    
    def delete_by_id(self, record_id: int) -> bool:
        """根据ID删除记录"""
        sql = f"DELETE FROM `{self.table_name}` WHERE id = %s"
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (record_id,))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    self.logger.debug(f"删除 {self.table_name} 记录，ID: {record_id}")
                else:
                    self.logger.warning(f"未找到要删除的记录，ID: {record_id}")
                return success
    
    def delete_where(self, conditions: Dict[str, Any]) -> int:
        """根据条件删除记录"""
        if not conditions:
            raise ValueError("删除条件不能为空，为了安全考虑")
        
        where_clause = ' AND '.join([f"`{k}` = %s" for k in conditions.keys()])
        sql = f"DELETE FROM `{self.table_name}` WHERE {where_clause}"
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, list(conditions.values()))
                conn.commit()
                count = cursor.rowcount
                self.logger.info(f"删除 {count} 条记录从 {self.table_name}")
                return count
    
    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """根据ID查找记录"""
        sql = f"SELECT * FROM `{self.table_name}` WHERE id = %s"
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (record_id,))
                return cursor.fetchone()
    
    def find_where(self, conditions: Dict[str, Any] = None, 
                   order_by: str = None, limit: int = None, 
                   offset: int = None) -> List[Dict[str, Any]]:
        """根据条件查找记录"""
        sql = f"SELECT * FROM `{self.table_name}`"
        params = []
        
        if conditions:
            where_clause = ' AND '.join([f"`{k}` = %s" for k in conditions.keys()])
            sql += f" WHERE {where_clause}"
            params.extend(conditions.values())
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
            if offset:
                sql += f" OFFSET {offset}"
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
    
    def find_all(self, order_by: str = None) -> List[Dict[str, Any]]:
        """查找所有记录"""
        return self.find_where(order_by=order_by)
    
    def count(self, conditions: Dict[str, Any] = None) -> int:
        """统计记录数量"""
        sql = f"SELECT COUNT(*) as count FROM `{self.table_name}`"
        params = []
        
        if conditions:
            where_clause = ' AND '.join([f"`{k}` = %s" for k in conditions.keys()])
            sql += f" WHERE {where_clause}"
            params.extend(conditions.values())
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()
                return result['count'] if result else 0
    
    def exists(self, conditions: Dict[str, Any]) -> bool:
        """检查记录是否存在"""
        return self.count(conditions) > 0
    
    def find_one_where(self, conditions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """根据条件查找单条记录"""
        results = self.find_where(conditions, limit=1)
        return results[0] if results else None
    
    def execute_raw_sql(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """执行原生SQL查询"""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchall()
    
    def execute_raw_sql_single(self, sql: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """执行原生SQL查询，返回单条记录"""
        results = self.execute_raw_sql(sql, params)
        return results[0] if results else None
    
    def to_dataframe(self, conditions: Dict[str, Any] = None, 
                    order_by: str = None) -> pd.DataFrame:
        """将查询结果转换为DataFrame"""
        data = self.find_where(conditions, order_by)
        return pd.DataFrame(data)
    
    def batch_operation(self, operations: List[callable]):
        """批量操作（事务）"""
        with self.db_manager.get_connection() as conn:
            try:
                for operation in operations:
                    operation(conn)
                conn.commit()
                self.logger.info(f"批量操作成功执行 {len(operations)} 个操作")
            except Exception as e:
                conn.rollback()
                self.logger.error(f"批量操作失败，已回滚: {e}")
                raise
    
    def truncate_table(self):
        """清空表数据"""
        sql = f"TRUNCATE TABLE `{self.table_name}`"
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                self.logger.warning(f"表 {self.table_name} 已被清空")
    
    def drop_table(self):
        """删除表"""
        sql = f"DROP TABLE IF EXISTS `{self.table_name}`"
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                self.logger.warning(f"表 {self.table_name} 已被删除")
