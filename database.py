"""
数据库模块 - 负责SQLite数据库的创建、读写操作
"""
import sqlite3
import os
from typing import List, Dict, Optional, Tuple


class CorpusDatabase:
    """语料数据库管理类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径（可选，默认使用用户主目录）
        """
        if db_path is None:
            # 使用用户主目录下的 .fieldnote 文件夹
            home_dir = os.path.expanduser("~")
            data_dir = os.path.join(home_dir, ".fieldnote")
            # 如果目录不存在，创建它
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "corpus.db")
        else:
            self.db_path = db_path
        
        self.connection = None
        self.cursor = None
        self._connect()
        self._create_table()
    
    def _connect(self):
        """建立数据库连接"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        self.cursor = self.connection.cursor()
    
    def _create_table(self):
        """创建语料表（如果不存在）"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS corpus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                example_id TEXT,
                source_text TEXT,
                gloss TEXT,
                translation TEXT,
                notes TEXT,
                source_text_cn TEXT,
                gloss_cn TEXT,
                translation_cn TEXT
            )
        """)
        self.connection.commit()
        
        # 检查并添加新字段（用于数据库迁移）
        self._migrate_add_chinese_fields()
    
    def _migrate_add_chinese_fields(self):
        """数据库迁移：添加汉字字段（如果不存在）"""
        try:
            # 检查是否已有汉字字段
            self.cursor.execute("PRAGMA table_info(corpus)")
            columns = [row[1] for row in self.cursor.fetchall()]
            
            # 添加缺失的字段
            if 'source_text_cn' not in columns:
                self.cursor.execute("ALTER TABLE corpus ADD COLUMN source_text_cn TEXT")
            if 'gloss_cn' not in columns:
                self.cursor.execute("ALTER TABLE corpus ADD COLUMN gloss_cn TEXT")
            if 'translation_cn' not in columns:
                self.cursor.execute("ALTER TABLE corpus ADD COLUMN translation_cn TEXT")
            
            self.connection.commit()
        except Exception as e:
            print(f"数据库迁移失败: {e}")
    
    def insert_entry(self, example_id: str, source_text: str, gloss: str, 
                     translation: str, notes: str = "", 
                     source_text_cn: str = "", gloss_cn: str = "", 
                     translation_cn: str = "") -> int:
        """
        插入一条语料记录
        
        Args:
            example_id: 例句编号
            source_text: 原文
            gloss: 词汇分解/注释
            translation: 翻译
            notes: 备注
            source_text_cn: 原文(汉字)
            gloss_cn: 词汇分解(汉字)
            translation_cn: 翻译(汉字)
            
        Returns:
            新插入记录的ID
        """
        self.cursor.execute("""
            INSERT INTO corpus (example_id, source_text, gloss, translation, notes, 
                              source_text_cn, gloss_cn, translation_cn)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (example_id, source_text, gloss, translation, notes, 
              source_text_cn, gloss_cn, translation_cn))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def update_entry(self, entry_id: int, example_id: str, source_text: str, 
                     gloss: str, translation: str, notes: str = "",
                     source_text_cn: str = "", gloss_cn: str = "", 
                     translation_cn: str = "") -> bool:
        """
        更新一条语料记录
        
        Args:
            entry_id: 记录ID
            example_id: 例句编号
            source_text: 原文
            gloss: 词汇分解/注释
            translation: 翻译
            notes: 备注
            source_text_cn: 原文(汉字)
            gloss_cn: 词汇分解(汉字)
            translation_cn: 翻译(汉字)
            
        Returns:
            是否更新成功
        """
        self.cursor.execute("""
            UPDATE corpus 
            SET example_id = ?, source_text = ?, gloss = ?, translation = ?, notes = ?,
                source_text_cn = ?, gloss_cn = ?, translation_cn = ?
            WHERE id = ?
        """, (example_id, source_text, gloss, translation, notes, 
              source_text_cn, gloss_cn, translation_cn, entry_id))
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    def delete_entry(self, entry_id: int) -> bool:
        """
        删除一条语料记录
        
        Args:
            entry_id: 记录ID
            
        Returns:
            是否删除成功
        """
        self.cursor.execute("DELETE FROM corpus WHERE id = ?", (entry_id,))
        self.connection.commit()
        return self.cursor.rowcount > 0
    
    def get_entry(self, entry_id: int) -> Optional[Dict]:
        """
        获取单条语料记录
        
        Args:
            entry_id: 记录ID
            
        Returns:
            语料记录字典，如果不存在则返回None
        """
        self.cursor.execute("SELECT * FROM corpus WHERE id = ?", (entry_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_entries(self) -> List[Dict]:
        """
        获取所有语料记录
        
        Returns:
            语料记录列表
        """
        self.cursor.execute("SELECT * FROM corpus ORDER BY id")
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def search_entries(self, field: str, keyword: str, 
                       use_regex: bool = False) -> List[Dict]:
        """
        搜索语料记录
        
        Args:
            field: 搜索字段 (example_id, source_text, gloss, translation, notes)
            keyword: 搜索关键词
            use_regex: 是否使用正则表达式（暂不支持SQLite原生正则）
            
        Returns:
            符合条件的语料记录列表
        """
        # SQLite的LIKE进行模糊搜索
        if field == "all":
            # 搜索所有字段
            query = """
                SELECT * FROM corpus 
                WHERE example_id LIKE ? OR source_text LIKE ? 
                   OR gloss LIKE ? OR translation LIKE ? OR notes LIKE ?
                ORDER BY id
            """
            pattern = f"%{keyword}%"
            self.cursor.execute(query, (pattern, pattern, pattern, pattern, pattern))
        else:
            # 搜索特定字段
            allowed_fields = ["example_id", "source_text", "gloss", "translation", "notes"]
            if field not in allowed_fields:
                return []
            
            query = f"SELECT * FROM corpus WHERE {field} LIKE ? ORDER BY id"
            self.cursor.execute(query, (f"%{keyword}%",))
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_count(self) -> int:
        """
        获取语料总数
        
        Returns:
            语料记录总数
        """
        self.cursor.execute("SELECT COUNT(*) FROM corpus")
        return self.cursor.fetchone()[0]
    
    def import_from_list(self, entries: List[Dict]) -> int:
        """
        批量导入语料
        
        Args:
            entries: 语料记录列表，每个元素为字典
            
        Returns:
            成功导入的记录数
        """
        count = 0
        for entry in entries:
            try:
                self.insert_entry(
                    example_id=entry.get("example_id", ""),
                    source_text=entry.get("source_text", ""),
                    gloss=entry.get("gloss", ""),
                    translation=entry.get("translation", ""),
                    notes=entry.get("notes", ""),
                    source_text_cn=entry.get("source_text_cn", ""),
                    gloss_cn=entry.get("gloss_cn", ""),
                    translation_cn=entry.get("translation_cn", "")
                )
                count += 1
            except Exception as e:
                print(f"导入记录失败: {e}")
                continue
        return count
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()

