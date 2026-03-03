"""
数据库模块 - 负责SQLite数据库的创建、读写操作
"""
import sqlite3
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple

# 当前 schema 版本
SCHEMA_VERSION = 3


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
        self._run_migrations()

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
                translation_cn TEXT,
                entry_type TEXT DEFAULT 'sentence',
                group_id TEXT,
                group_name TEXT,
                speaker TEXT,
                turn_number INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)
        """)
        self.connection.commit()

    def _get_schema_version(self) -> int:
        """获取当前 schema 版本"""
        try:
            self.cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            row = self.cursor.fetchone()
            if row:
                return row[0]
        except Exception:
            pass
        return 0

    def _set_schema_version(self, version: int):
        """设置 schema 版本"""
        self.cursor.execute("DELETE FROM schema_version")
        self.cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        self.connection.commit()

    def _run_migrations(self):
        """统一的数据库迁移方法"""
        current = self._get_schema_version()

        if current < SCHEMA_VERSION:
            # 获取现有列名
            self.cursor.execute("PRAGMA table_info(corpus)")
            columns = [row[1] for row in self.cursor.fetchall()]

            try:
                # Migration 1: 添加中文字段
                if 'source_text_cn' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN source_text_cn TEXT")
                if 'gloss_cn' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN gloss_cn TEXT")
                if 'translation_cn' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN translation_cn TEXT")

                # Migration 2: 添加类型字段
                if 'entry_type' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN entry_type TEXT DEFAULT 'sentence'")
                if 'group_id' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN group_id TEXT")
                if 'group_name' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN group_name TEXT")
                if 'speaker' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN speaker TEXT")
                if 'turn_number' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN turn_number INTEGER")

                # Migration 3: 添加时间戳和标签字段
                if 'created_at' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN created_at TEXT")
                if 'updated_at' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN updated_at TEXT")
                if 'tags' not in columns:
                    self.cursor.execute("ALTER TABLE corpus ADD COLUMN tags TEXT DEFAULT ''")

                self._set_schema_version(SCHEMA_VERSION)
            except Exception as e:
                print(f"数据库迁移失败: {e}")

    def insert_entry(self, example_id: str, source_text: str, gloss: str,
                     translation: str, notes: str = "",
                     source_text_cn: str = "", gloss_cn: str = "",
                     translation_cn: str = "",
                     entry_type: str = "sentence", group_id: str = "",
                     group_name: str = "", speaker: str = "",
                     turn_number: int = None, tags: str = "") -> int:
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
            entry_type: 条目类型 (word/sentence/discourse/dialogue)
            group_id: 分组ID (语篇/对话)
            group_name: 分组名称 (语篇/对话)
            speaker: 说话人 (对话)
            turn_number: 话轮序号
            tags: 标签（逗号分隔）

        Returns:
            新插入记录的ID
        """
        now = datetime.now(timezone.utc).isoformat()
        self.cursor.execute("""
            INSERT INTO corpus (example_id, source_text, gloss, translation, notes,
                              source_text_cn, gloss_cn, translation_cn,
                              entry_type, group_id, group_name, speaker, turn_number,
                              created_at, updated_at, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (example_id, source_text, gloss, translation, notes,
              source_text_cn, gloss_cn, translation_cn,
              entry_type, group_id, group_name, speaker, turn_number,
              now, now, tags))
        self.connection.commit()
        return self.cursor.lastrowid

    def update_entry(self, entry_id: int, example_id: str, source_text: str,
                     gloss: str, translation: str, notes: str = "",
                     source_text_cn: str = "", gloss_cn: str = "",
                     translation_cn: str = "",
                     entry_type: str = "sentence", group_id: str = "",
                     group_name: str = "", speaker: str = "",
                     turn_number: int = None, tags: str = "") -> bool:
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
            entry_type: 条目类型
            group_id: 分组ID
            group_name: 分组名称
            speaker: 说话人
            turn_number: 话轮序号
            tags: 标签（逗号分隔）

        Returns:
            是否更新成功
        """
        now = datetime.now(timezone.utc).isoformat()
        self.cursor.execute("""
            UPDATE corpus
            SET example_id = ?, source_text = ?, gloss = ?, translation = ?, notes = ?,
                source_text_cn = ?, gloss_cn = ?, translation_cn = ?,
                entry_type = ?, group_id = ?, group_name = ?, speaker = ?, turn_number = ?,
                updated_at = ?, tags = ?
            WHERE id = ?
        """, (example_id, source_text, gloss, translation, notes,
              source_text_cn, gloss_cn, translation_cn,
              entry_type, group_id, group_name, speaker, turn_number,
              now, tags, entry_id))
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
                       use_regex: bool = False, entry_type: str = None,
                       tags: List[str] = None) -> List[Dict]:
        """
        搜索语料记录

        Args:
            field: 搜索字段 (example_id, source_text, gloss, translation, notes)
            keyword: 搜索关键词
            use_regex: 是否使用正则表达式（暂不支持SQLite原生正则）
            entry_type: 数据类型筛选 (word, sentence, discourse, dialogue)，None表示全部类型
            tags: 标签筛选列表，None表示不按标签筛选

        Returns:
            符合条件的语料记录列表
        """
        # SQLite的LIKE进行模糊搜索
        if field == "all":
            # 搜索所有字段
            if entry_type:
                query = """
                    SELECT * FROM corpus
                    WHERE (example_id LIKE ? OR source_text LIKE ?
                       OR gloss LIKE ? OR translation LIKE ? OR notes LIKE ?)
                       AND entry_type = ?
                    ORDER BY id
                """
                pattern = f"%{keyword}%"
                self.cursor.execute(query, (pattern, pattern, pattern, pattern, pattern, entry_type))
            else:
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

            if entry_type:
                query = f"SELECT * FROM corpus WHERE {field} LIKE ? AND entry_type = ? ORDER BY id"
                self.cursor.execute(query, (f"%{keyword}%", entry_type))
            else:
                query = f"SELECT * FROM corpus WHERE {field} LIKE ? ORDER BY id"
                self.cursor.execute(query, (f"%{keyword}%",))

        rows = self.cursor.fetchall()
        results = [dict(row) for row in rows]

        # 标签筛选（在内存中过滤）
        if tags:
            filtered = []
            for entry in results:
                entry_tags = [t.strip() for t in (entry.get('tags', '') or '').split(',') if t.strip()]
                if any(t in entry_tags for t in tags):
                    filtered.append(entry)
            results = filtered

        return results

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
                    translation_cn=entry.get("translation_cn", ""),
                    entry_type=entry.get("entry_type", "sentence"),
                    group_id=entry.get("group_id", ""),
                    group_name=entry.get("group_name", ""),
                    speaker=entry.get("speaker", ""),
                    turn_number=entry.get("turn_number", None),
                    tags=entry.get("tags", "")
                )
                count += 1
            except Exception as e:
                print(f"导入记录失败: {e}")
                continue
        return count

    def get_entries_by_type(self, entry_type: str) -> List[Dict]:
        """
        按类型获取语料记录

        Args:
            entry_type: 条目类型 (word/sentence/discourse/dialogue)

        Returns:
            符合类型的语料记录列表
        """
        self.cursor.execute(
            "SELECT * FROM corpus WHERE entry_type = ? ORDER BY id",
            (entry_type,)
        )
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def get_groups_by_type(self, entry_type: str) -> List[Dict]:
        """
        获取指定类型的所有分组（语篇或对话）

        Args:
            entry_type: discourse 或 dialogue

        Returns:
            分组列表，每个包含 group_id, group_name, count
        """
        self.cursor.execute("""
            SELECT group_id, group_name, COUNT(*) as count
            FROM corpus
            WHERE entry_type = ? AND group_id IS NOT NULL AND group_id != ''
            GROUP BY group_id, group_name
            ORDER BY group_id
        """, (entry_type,))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def get_entries_by_group(self, group_id: str) -> List[Dict]:
        """
        获取某个分组（语篇/对话）的所有条目

        Args:
            group_id: 分组ID

        Returns:
            该分组的所有语料记录
        """
        self.cursor.execute("""
            SELECT * FROM corpus
            WHERE group_id = ?
            ORDER BY turn_number, id
        """, (group_id,))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def get_next_group_id(self, entry_type: str) -> str:
        """
        生成下一个分组ID

        Args:
            entry_type: discourse 或 dialogue

        Returns:
            新的分组ID (如 DSC001, DLG001)
        """
        prefix = "DSC" if entry_type == "discourse" else "DLG"
        self.cursor.execute("""
            SELECT group_id FROM corpus
            WHERE entry_type = ? AND group_id LIKE ?
            ORDER BY group_id DESC LIMIT 1
        """, (entry_type, f"{prefix}%"))
        row = self.cursor.fetchone()

        if row and row[0]:
            # 提取数字部分并加1
            last_id = row[0]
            try:
                num = int(last_id[3:]) + 1
                return f"{prefix}{num:03d}"
            except:
                return f"{prefix}001"
        return f"{prefix}001"

    def delete_group(self, group_id: str) -> bool:
        """
        删除整个分组（语篇/对话）的所有条目

        Args:
            group_id: 分组ID

        Returns:
            是否删除成功
        """
        self.cursor.execute("DELETE FROM corpus WHERE group_id = ?", (group_id,))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def rename_group(self, group_id: str, new_name: str) -> bool:
        """
        重命名分组

        Args:
            group_id: 分组ID
            new_name: 新名称

        Returns:
            是否重命名成功
        """
        self.cursor.execute("""
            UPDATE corpus SET group_name = ? WHERE group_id = ?
        """, (new_name, group_id))
        self.connection.commit()
        return self.cursor.rowcount > 0

    def example_id_exists(self, example_id: str, exclude_id: int = None) -> bool:
        """
        检查 example_id 是否已存在

        Args:
            example_id: 要检查的例句编号
            exclude_id: 排除的记录ID（用于更新时排除自身）

        Returns:
            是否已存在
        """
        if exclude_id is not None:
            self.cursor.execute(
                "SELECT COUNT(*) FROM corpus WHERE example_id = ? AND id != ?",
                (example_id, exclude_id)
            )
        else:
            self.cursor.execute(
                "SELECT COUNT(*) FROM corpus WHERE example_id = ?",
                (example_id,)
            )
        return self.cursor.fetchone()[0] > 0

    def get_stats(self) -> Dict:
        """
        获取语料统计信息

        Returns:
            {total, by_type: {word, sentence, discourse, dialogue},
             today_count, week_count}
        """
        # 总计
        self.cursor.execute("SELECT COUNT(*) FROM corpus")
        total = self.cursor.fetchone()[0]

        # 按类型统计
        by_type = {}
        for t in ['word', 'sentence', 'discourse', 'dialogue']:
            self.cursor.execute("SELECT COUNT(*) FROM corpus WHERE entry_type = ?", (t,))
            by_type[t] = self.cursor.fetchone()[0]

        # 今日新增
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        self.cursor.execute(
            "SELECT COUNT(*) FROM corpus WHERE created_at LIKE ?",
            (f"{today}%",)
        )
        today_count = self.cursor.fetchone()[0]

        # 本周新增
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        self.cursor.execute(
            "SELECT COUNT(*) FROM corpus WHERE created_at >= ?",
            (week_ago,)
        )
        week_count = self.cursor.fetchone()[0]

        return {
            'total': total,
            'by_type': by_type,
            'today_count': today_count,
            'week_count': week_count
        }

    def get_word_frequencies(self, entry_type: str = None, limit: int = 20) -> List[Tuple[str, int]]:
        """
        从 source_text 中分词统计词频

        Args:
            entry_type: 可选的类型筛选
            limit: 返回前N个高频词

        Returns:
            [(词, 频次), ...]
        """
        if entry_type:
            self.cursor.execute(
                "SELECT source_text FROM corpus WHERE entry_type = ?",
                (entry_type,)
            )
        else:
            self.cursor.execute("SELECT source_text FROM corpus")

        rows = self.cursor.fetchall()
        word_counts: Dict[str, int] = {}

        for row in rows:
            text = row[0] or ''
            for word in text.strip().split():
                word = word.strip()
                if word:
                    word_counts[word] = word_counts.get(word, 0) + 1

        # 按频次降序排列
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:limit]

    def get_all_tags(self) -> List[str]:
        """
        返回所有使用过的唯一标签列表

        Returns:
            标签列表
        """
        self.cursor.execute("SELECT tags FROM corpus WHERE tags IS NOT NULL AND tags != ''")
        rows = self.cursor.fetchall()

        tag_set = set()
        for row in rows:
            for tag in row[0].split(','):
                tag = tag.strip()
                if tag:
                    tag_set.add(tag)

        return sorted(tag_set)

    def get_entries_by_tags(self, tags: List[str]) -> List[Dict]:
        """
        返回包含任意一个指定标签的条目

        Args:
            tags: 标签列表

        Returns:
            符合条件的语料记录列表
        """
        if not tags:
            return []

        # 获取所有有标签的条目，在内存中过滤
        self.cursor.execute(
            "SELECT * FROM corpus WHERE tags IS NOT NULL AND tags != '' ORDER BY id"
        )
        rows = self.cursor.fetchall()

        results = []
        for row in rows:
            entry = dict(row)
            entry_tags = [t.strip() for t in (entry.get('tags', '') or '').split(',') if t.strip()]
            if any(t in entry_tags for t in tags):
                results.append(entry)

        return results

    def get_tag_distribution(self) -> List[Tuple[str, int]]:
        """
        获取标签分布统计

        Returns:
            [(标签, 数量), ...] 按数量降序
        """
        self.cursor.execute("SELECT tags FROM corpus WHERE tags IS NOT NULL AND tags != ''")
        rows = self.cursor.fetchall()

        tag_counts: Dict[str, int] = {}
        for row in rows:
            for tag in row[0].split(','):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
