"""
导出模块 - 负责将语料导出为各种格式
"""
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import List, Dict


class TextFormatter:
    """文本格式化类 - 生成对齐的语言学格式文本"""
    
    @staticmethod
    def calculate_display_width(text: str) -> int:
        """
        计算文本的显示宽度（考虑等宽字体）
        在等宽字体中：
        - 中文、日文等宽字符：2
        - 英文、数字、标点：1
        - 上标数字（音调）：0.5（计为1，但多个上标算一起）
        """
        import unicodedata
        
        width = 0
        i = 0
        text_len = len(text)
        
        while i < text_len:
            char = text[i]
            code = ord(char)
            
            # 中日韩统一表意文字
            if 0x4E00 <= code <= 0x9FFF:
                width += 2
            # 中日韩扩展
            elif 0x3400 <= code <= 0x4DBF:
                width += 2
            # 全角字符
            elif 0xFF00 <= code <= 0xFFEF:
                width += 2
            # 上标数字（音调标记）- 统一计为0.5宽度
            elif 0x2070 <= code <= 0x209F or 0x00B2 <= code <= 0x00B3:
                # 连续的上标数字一起计算
                superscript_count = 0
                while i < text_len and (0x2070 <= ord(text[i]) <= 0x209F or 0x00B2 <= ord(text[i]) <= 0x00B3):
                    superscript_count += 1
                    i += 1
                i -= 1  # 回退一个，因为循环会+1
                # 每2个上标字符算1个宽度
                width += (superscript_count + 1) // 2
            # 组合变音符号（紧跟在字母后面的）
            elif unicodedata.category(char) in ['Mn', 'Mc', 'Me']:
                width += 0
            # 其他字符
            else:
                width += 1
            
            i += 1
        
        return width
    
    @staticmethod
    def align_words(source_words: List[str], gloss_words: List[str]) -> tuple:
        """
        对齐原文和词汇分解（紧凑型完美左对齐）
        
        Args:
            source_words: 原文词列表
            gloss_words: 词汇分解列表
            
        Returns:
            (对齐后的原文行, 对齐后的gloss行)
        """
        # 确保两个列表长度相同
        max_len = max(len(source_words), len(gloss_words))
        source_words = source_words + [''] * (max_len - len(source_words))
        gloss_words = gloss_words + [''] * (max_len - len(gloss_words))
        
        # 计算每个位置需要的实际宽度（紧凑模式）
        column_widths = []
        for src, gls in zip(source_words, gloss_words):
            # 计算字符长度（包括上标）
            src_len = len(src)
            gls_len = len(gls)
            
            # 取较大者，并加上最少2个空格作为间距
            col_width = max(src_len, gls_len) + 2
            column_widths.append(col_width)
        
        # 对齐每一列
        aligned_source_parts = []
        aligned_gloss_parts = []
        
        for src, gls, col_width in zip(source_words, gloss_words, column_widths):
            # 左对齐，右侧填充空格到列宽
            src_padded = src.ljust(col_width)
            gls_padded = gls.ljust(col_width)
            
            aligned_source_parts.append(src_padded)
            aligned_gloss_parts.append(gls_padded)
        
        # 连接所有列
        return (''.join(aligned_source_parts), ''.join(aligned_gloss_parts))
    
    @staticmethod
    def format_entry(entry: Dict, show_numbering: bool = True, number_format: str = "()",
                    max_words_per_line: int = 10, include_chinese: bool = False) -> str:
        """
        格式化单条语料为标准语言学格式（Leipzig Glossing Rules）
        支持长句自动分行
        
        Args:
            entry: 语料记录
            show_numbering: 是否显示编号
            number_format: 编号格式 "()" 或 "."
            max_words_per_line: 每行最多显示的词数（默认10）
            include_chinese: 是否包含汉字注释字段
            
        Returns:
            格式化后的文本
        """
        lines = []
        
        # 准备编号
        numbering_text = ""
        if show_numbering:
            example_id = entry.get('example_id', '')
            if example_id:
                if number_format == "()":
                    numbering_text = f"({example_id}) "
                else:
                    numbering_text = f"{example_id}. "
            else:
                entry_id = entry.get('id', '')
                if number_format == "()":
                    numbering_text = f"({entry_id}) "
                else:
                    numbering_text = f"{entry_id}. "
        
        # 分词（按空格分割）
        source_text = entry.get('source_text', '').strip()
        gloss = entry.get('gloss', '').strip()
        translation = entry.get('translation', '').strip()
        notes = entry.get('notes', '').strip()
        
        # 汉字字段（如果包含）
        source_text_cn = entry.get('source_text_cn', '').strip() if include_chinese else ""
        gloss_cn = entry.get('gloss_cn', '').strip() if include_chinese else ""
        translation_cn = entry.get('translation_cn', '').strip() if include_chinese else ""
        
        # 计算缩进空格数（编号的长度）
        indent_spaces = ' ' * len(numbering_text)
        
        # 原文行和注释行 - 进行词对齐（支持自动分行）
        source_has_words = len(source_text.split()) > 1
        gloss_has_words = len(gloss.split()) > 1
        
        if source_has_words and gloss_has_words:
            # 多词情况：编号单独一行，然后词对齐
            if numbering_text:
                lines.append(numbering_text.rstrip())
            
            source_words = source_text.split()
            gloss_words = gloss.split()
            
            # 如果原文最后一个词是单独的句号，将其合并到前一个词
            if len(source_words) > 1 and source_words[-1] == '.':
                source_words[-2] = source_words[-2] + '.'
                source_words.pop()
            
            # 确保词数相同
            max_len = max(len(source_words), len(gloss_words))
            source_words = source_words + [''] * (max_len - len(source_words))
            gloss_words = gloss_words + [''] * (max_len - len(gloss_words))
            
            # 如果词数超过每行最大值，分行显示
            if len(source_words) > max_words_per_line:
                # 分批处理
                for i in range(0, len(source_words), max_words_per_line):
                    batch_source = source_words[i:i + max_words_per_line]
                    batch_gloss = gloss_words[i:i + max_words_per_line]
                    
                    aligned_source, aligned_gloss = TextFormatter.align_words(batch_source, batch_gloss)
                    lines.append(f"    {aligned_source}")
                    lines.append(f"    {aligned_gloss}")
                    
                    # 如果还有下一批，添加空行分隔
                    if i + max_words_per_line < len(source_words):
                        lines.append("")
            else:
                # 一行能显示完
                aligned_source, aligned_gloss = TextFormatter.align_words(source_words, gloss_words)
                lines.append(f"    {aligned_source}")
                # 原文(汉字) 紧跟原文
                if source_text_cn:
                    lines.append(f"    【原文(汉字)】{source_text_cn}")
                
                lines.append(f"    {aligned_gloss}")
                # 词汇分解(汉字) 紧跟词汇分解
                if gloss_cn:
                    lines.append(f"    【词汇分解(汉字)】{gloss_cn}")
            
            # 翻译行
            if translation:
                if notes:
                    lines.append(f"    '{translation}' ({notes})")
                else:
                    lines.append(f"    '{translation}'")
            elif notes:
                lines.append(f"    ({notes})")
            
            # 翻译(汉字) 紧跟翻译
            if translation_cn:
                lines.append(f"    【翻译(汉字)】{translation_cn}")
        else:
            # 单词情况：编号和原文在同一行
            lines.append(f"{numbering_text}{source_text}")
            # 原文(汉字) 紧跟原文
            if source_text_cn:
                lines.append(f"{indent_spaces}【原文(汉字)】{source_text_cn}")
            
            # gloss 行（缩进对齐）
            if gloss:
                lines.append(f"{indent_spaces}{gloss}")
            # 词汇分解(汉字) 紧跟词汇分解
            if gloss_cn:
                lines.append(f"{indent_spaces}【词汇分解(汉字)】{gloss_cn}")
            
            # 翻译行（缩进对齐）
            if translation:
                if notes:
                    lines.append(f"{indent_spaces}'{translation}' ({notes})")
                else:
                    lines.append(f"{indent_spaces}'{translation}'")
            elif notes:
                lines.append(f"{indent_spaces}({notes})")
            # 翻译(汉字) 紧跟翻译
            if translation_cn:
                lines.append(f"{indent_spaces}【翻译(汉字)】{translation_cn}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def format_entries(entries: List[Dict], show_numbering: bool = True, 
                      number_format: str = "()", include_chinese: bool = False) -> str:
        """
        格式化多条语料
        
        Args:
            entries: 语料记录列表
            show_numbering: 是否显示编号
            number_format: 编号格式 "()" 或 "."
            include_chinese: 是否包含汉字注释字段
            
        Returns:
            格式化后的文本
        """
        formatted = []
        for entry in entries:
            formatted.append(TextFormatter.format_entry(entry, show_numbering, number_format, 
                                                       include_chinese=include_chinese))
            formatted.append('')  # 空行分隔每条语料
        
        return '\n'.join(formatted)


class WordExporter:
    """Word文档导出类"""
    
    def __init__(self):
        """初始化导出器"""
        self.doc = Document()
    
    def export(self, entries: List[Dict], output_path: str, 
               table_width: float = 5.0,
               font_size: int = 10,
               line_spacing: float = 1.15,
               show_numbering: bool = True,
               entries_per_page: int = 10,
               include_chinese: bool = False) -> bool:
        """
        导出语料到Word文档（词对词对齐，透明表格）
        
        Args:
            entries: 语料记录列表
            output_path: 输出文件路径
            table_width: 表格宽度（英寸）
            font_size: 字体大小（磅）
            line_spacing: 行距
            show_numbering: 是否显示编号
            entries_per_page: 每页语料数（暂未实现分页）
            include_chinese: 是否包含汉字注释字段
            
        Returns:
            是否导出成功
        """
        try:
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
            
            self.doc = Document()
            
            for idx, entry in enumerate(entries, 1):
                # 准备编号（如果需要）
                numbering_text = ""
                if show_numbering:
                    example_id = entry.get('example_id', '')
                    if example_id:
                        numbering_text = f"({example_id}) "
                    else:
                        numbering_text = f"({idx}) "
                
                # 分词
                source_text = entry.get('source_text', '').strip()
                gloss = entry.get('gloss', '').strip()
                translation = entry.get('translation', '').strip()
                notes = entry.get('notes', '').strip()
                
                # 汉字字段（如果包含）
                source_text_cn = entry.get('source_text_cn', '').strip() if include_chinese else ""
                gloss_cn = entry.get('gloss_cn', '').strip() if include_chinese else ""
                translation_cn = entry.get('translation_cn', '').strip() if include_chinese else ""
                
                # 如果有多个词（分词后长度>1），进行词对齐
                source_has_words = ' ' in source_text and len(source_text.split()) > 1
                gloss_has_words = ' ' in gloss and len(gloss.split()) > 1
                if source_has_words and gloss_has_words:
                    source_words = source_text.split()
                    gloss_words = gloss.split()
                    
                    # 如果原文最后一个词是单独的句号，将其合并到前一个词
                    if len(source_words) > 1 and source_words[-1] == '.':
                        source_words[-2] = source_words[-2] + '.'
                        source_words.pop()
                    
                    # 确保词数相同
                    max_len = max(len(source_words), len(gloss_words))
                    source_words = source_words + [''] * (max_len - len(source_words))
                    gloss_words = gloss_words + [''] * (max_len - len(gloss_words))
                    
                    # 创建透明表格：3行 x N列（原文、注释、翻译）
                    table = self.doc.add_table(rows=3, cols=max_len)
                    
                    # 移除所有边框（透明表格）
                    tbl = table._tbl
                    tblPr = tbl.tblPr
                    if tblPr is None:
                        tblPr = OxmlElement('w:tblPr')
                        tbl.insert(0, tblPr)
                    
                    # 设置边框为无
                    tblBorders = OxmlElement('w:tblBorders')
                    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                        border = OxmlElement(f'w:{border_name}')
                        border.set(qn('w:val'), 'none')
                        border.set(qn('w:sz'), '0')
                        border.set(qn('w:space'), '0')
                        border.set(qn('w:color'), 'auto')
                        tblBorders.append(border)
                    tblPr.append(tblBorders)
                    
                    # 设置表格布局为固定宽度（等宽列）
                    tblLayout = OxmlElement('w:tblLayout')
                    tblLayout.set(qn('w:type'), 'fixed')
                    tblPr.append(tblLayout)
                    
                    # 计算每列的宽度（平均分配）
                    from docx.shared import Cm
                    total_width = Cm(16)  # 总宽度16厘米
                    col_width = total_width / max_len
                    
                    # 设置每列的宽度
                    for col_idx in range(max_len):
                        for row in table.rows:
                            cell = row.cells[col_idx]
                            cell.width = col_width
                    
                    # 设置所有行为根据内容自动调整高度
                    for row in table.rows:
                        tr = row._tr
                        trPr = tr.get_or_add_trPr()
                        # 移除固定高度设置（如果有）
                        trHeight = trPr.find(qn('w:trHeight'))
                        if trHeight is not None:
                            trPr.remove(trHeight)
                        # 添加自动调整高度设置
                        trHeight = OxmlElement('w:trHeight')
                        trHeight.set(qn('w:hRule'), 'auto')  # 根据内容自动调整
                        trPr.append(trHeight)
                    
                    # 填充第一行（原文）
                    for col_idx, word in enumerate(source_words):
                        cell = table.rows[0].cells[col_idx]
                        # 第一个单元格加上编号
                        if col_idx == 0 and numbering_text:
                            cell.text = numbering_text + word
                        else:
                            cell.text = word
                        # 设置单元格垂直对齐为顶部
                        tc = cell._tc
                        tcPr = tc.get_or_add_tcPr()
                        vAlign = OxmlElement('w:vAlign')
                        vAlign.set(qn('w:val'), 'top')
                        tcPr.append(vAlign)
                        # 设置单元格格式
                        for paragraph in cell.paragraphs:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            for run in paragraph.runs:
                                run.font.size = Pt(font_size)
                    
                    # 填充第二行（注释）
                    for col_idx, word in enumerate(gloss_words):
                        cell = table.rows[1].cells[col_idx]
                        cell.text = word
                        # 设置单元格垂直对齐为顶部
                        tc = cell._tc
                        tcPr = tc.get_or_add_tcPr()
                        vAlign = OxmlElement('w:vAlign')
                        vAlign.set(qn('w:val'), 'top')
                        tcPr.append(vAlign)
                        # 设置单元格格式
                        for paragraph in cell.paragraphs:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            for run in paragraph.runs:
                                run.font.size = Pt(font_size)
                    
                    # 填充第三行（翻译）- 合并所有列
                    if translation:
                        # 合并第三行的所有单元格
                        merged_cell = table.rows[2].cells[0]
                        if max_len > 1:
                            for col_idx in range(1, max_len):
                                merged_cell.merge(table.rows[2].cells[col_idx])
                        
                        merged_cell.text = f"'{translation}'"
                        # 设置单元格垂直对齐为顶部
                        tc = merged_cell._tc
                        tcPr = tc.get_or_add_tcPr()
                        vAlign = OxmlElement('w:vAlign')
                        vAlign.set(qn('w:val'), 'top')
                        tcPr.append(vAlign)
                        for paragraph in merged_cell.paragraphs:
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            for run in paragraph.runs:
                                run.font.size = Pt(font_size)
                    
                    # 汉字字段（多词情况，表格之后紧跟）
                    if source_text_cn:
                        p_cn = self.doc.add_paragraph(f"    【原文(汉字)】{source_text_cn}")
                        p_cn.runs[0].font.size = Pt(font_size - 1)
                        p_cn.paragraph_format.space_after = Pt(2)
                        p_cn.paragraph_format.space_before = Pt(0)
                    if gloss_cn:
                        p_cn = self.doc.add_paragraph(f"    【词汇分解(汉字)】{gloss_cn}")
                        p_cn.runs[0].font.size = Pt(font_size - 1)
                        p_cn.paragraph_format.space_after = Pt(2)
                        p_cn.paragraph_format.space_before = Pt(0)
                    if translation_cn:
                        p_cn = self.doc.add_paragraph(f"    【翻译(汉字)】{translation_cn}")
                        p_cn.runs[0].font.size = Pt(font_size - 1)
                        p_cn.paragraph_format.space_after = Pt(2)
                        p_cn.paragraph_format.space_before = Pt(0)
                    
                else:
                    # 如果没有分词，使用段落格式（不用表格）
                    from docx.shared import Cm
                    
                    # 计算缩进量（编号的宽度）
                    # 假设每个字符约 0.15cm，根据编号长度计算
                    indent_cm = len(numbering_text) * 0.15 if numbering_text else 0
                    
                    # 第一行：编号 + 原文
                    p1 = self.doc.add_paragraph()
                    if numbering_text:
                        p1.add_run(numbering_text).font.size = Pt(font_size)
                    p1.add_run(source_text).font.size = Pt(font_size)
                    p1.paragraph_format.space_after = Pt(2)
                    p1.paragraph_format.space_before = Pt(0)
                    
                    # 原文(汉字) 紧跟原文
                    if source_text_cn:
                        p_cn = self.doc.add_paragraph(f"【原文(汉字)】{source_text_cn}")
                        p_cn.runs[0].font.size = Pt(font_size - 1)
                        p_cn.paragraph_format.left_indent = Cm(indent_cm)
                        p_cn.paragraph_format.space_after = Pt(2)
                        p_cn.paragraph_format.space_before = Pt(0)
                    
                    # 第二行：gloss（左缩进与原文对齐）
                    if gloss:
                        p2 = self.doc.add_paragraph(gloss)
                        p2.runs[0].font.size = Pt(font_size)
                        p2.paragraph_format.left_indent = Cm(indent_cm)
                        p2.paragraph_format.space_after = Pt(2)
                        p2.paragraph_format.space_before = Pt(0)
                    
                    # 词汇分解(汉字) 紧跟词汇分解
                    if gloss_cn:
                        p_cn = self.doc.add_paragraph(f"【词汇分解(汉字)】{gloss_cn}")
                        p_cn.runs[0].font.size = Pt(font_size - 1)
                        p_cn.paragraph_format.left_indent = Cm(indent_cm)
                        p_cn.paragraph_format.space_after = Pt(2)
                        p_cn.paragraph_format.space_before = Pt(0)
                    
                    # 第三行：翻译（左缩进与原文对齐）
                    if translation:
                        p3 = self.doc.add_paragraph(f"'{translation}'")
                        p3.runs[0].font.size = Pt(font_size)
                        p3.paragraph_format.left_indent = Cm(indent_cm)
                        p3.paragraph_format.space_after = Pt(2)
                        p3.paragraph_format.space_before = Pt(0)
                    
                    # 翻译(汉字) 紧跟翻译
                    if translation_cn:
                        p_cn = self.doc.add_paragraph(f"【翻译(汉字)】{translation_cn}")
                        p_cn.runs[0].font.size = Pt(font_size - 1)
                        p_cn.paragraph_format.left_indent = Cm(indent_cm)
                        p_cn.paragraph_format.space_after = Pt(2)
                        p_cn.paragraph_format.space_before = Pt(0)
                
                # 添加备注（在表格外，与原文第一个词对齐）
                if notes:
                    note_p = self.doc.add_paragraph(f"    ({notes})")
                    note_p.runs[0].font.size = Pt(font_size - 1)
                    note_p.runs[0].italic = True
                
                # 添加段落间距
                self.doc.add_paragraph()
            
            # 保存文档
            self.doc.save(output_path)
            return True
            
        except Exception as e:
            print(f"导出失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def export_custom_format(self, entries: List[Dict], output_path: str,
                            format_template: str = None) -> bool:
        """
        使用自定义格式导出
        
        Args:
            entries: 语料记录列表
            output_path: 输出文件路径
            format_template: 自定义格式模板（未来功能）
            
        Returns:
            是否导出成功
        """
        # 未来可扩展的自定义格式导出
        return self.export(entries, output_path)

