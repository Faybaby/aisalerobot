import json
import os
from typing import List, Dict, Any, Optional

class JsonDB:
    """
    简单的JSON文件数据库实现
    用于客户数据的持久化存储
    """
    
    def __init__(self, file_path: str):
        """
        初始化JSON数据库
        
        Args:
            file_path: JSON文件的相对路径
        """
        self.file_path = file_path
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.full_path = os.path.join(os.path.dirname(self.base_dir), file_path)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.full_path), exist_ok=True)
        
        # 如果文件不存在，创建空数组文件
        if not os.path.exists(self.full_path):
            with open(self.full_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        获取所有记录
        
        Returns:
            所有记录的列表
        """
        try:
            with open(self.full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单个记录
        
        Args:
            id: 记录ID
            
        Returns:
            匹配的记录或None
        """
        records = self.get_all()
        for record in records:
            if record.get('id') == id:
                return record
        return None
    
    def add(self, record: Dict[str, Any]) -> bool:
        """
        添加新记录
        
        Args:
            record: 要添加的记录
            
        Returns:
            是否添加成功
        """
        records = self.get_all()
        records.append(record)
        return self._save(records)
    
    def update(self, record: Dict[str, Any]) -> bool:
        """
        更新记录
        
        Args:
            record: 要更新的记录（必须包含id字段）
            
        Returns:
            是否更新成功
        """
        if 'id' not in record:
            return False
            
        records = self.get_all()
        for i, existing_record in enumerate(records):
            if existing_record.get('id') == record['id']:
                records[i] = record
                return self._save(records)
        
        return False
    
    def delete(self, id: str) -> bool:
        """
        删除记录
        
        Args:
            id: 要删除的记录ID
            
        Returns:
            是否删除成功
        """
        records = self.get_all()
        initial_count = len(records)
        records = [r for r in records if r.get('id') != id]
        
        if len(records) < initial_count:
            return self._save(records)
        
        return False
    
    def _save(self, records: List[Dict[str, Any]]) -> bool:
        """
        保存记录到文件
        
        Args:
            records: 要保存的记录列表
            
        Returns:
            是否保存成功
        """
        try:
            with open(self.full_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False