"""
AI Prompt 模板 - 语言学专用 prompt 构建
"""
from typing import List, Dict, Tuple


# 莱比锡标注常用缩写表
LEIPZIG_ABBREVIATIONS = (
    "1 first person, 2 second person, 3 third person, "
    "SG singular, PL plural, DU dual, "
    "NOM nominative, ACC accusative, DAT dative, GEN genitive, ERG ergative, ABS absolutive, "
    "LOC locative, INS instrumental, COM comitative, ABL ablative, ALL allative, "
    "PST past, PRS present, FUT future, IPFV imperfective, PFV perfective, PROG progressive, "
    "NEG negation, Q question, IMP imperative, COND conditional, "
    "CLF classifier, DET determiner, DEF definite, INDEF indefinite, "
    "TOP topic, FOC focus, REL relative, COMP complementizer, QUOT quotative, "
    "CAUS causative, APPL applicative, PASS passive, REFL reflexive, RECP reciprocal, "
    "NMLZ nominalizer, ADV adverbializer, PTCP participle, INF infinitive, "
    "COP copula, AUX auxiliary, CONN connective, CONJ conjunction"
)


def _format_context_entries(entries: List[Dict]) -> str:
    """将 few-shot 上下文条目格式化为示例文本"""
    if not entries:
        return ""
    lines = []
    for i, entry in enumerate(entries, 1):
        src = (entry.get("source_text") or "").strip()
        gloss = (entry.get("gloss") or "").strip()
        trans = (entry.get("translation") or "").strip()
        src_cn = (entry.get("source_text_cn") or "").strip()
        if not src or not gloss:
            continue
        lines.append(f"例{i}:")
        lines.append(f"  原文: {src}")
        if src_cn:
            lines.append(f"  原文(汉字): {src_cn}")
        lines.append(f"  词汇分解: {gloss}")
        if trans:
            lines.append(f"  翻译: {trans}")
        lines.append("")
    return "\n".join(lines)


def build_gloss_prompt(source_text: str, context_entries: List[Dict],
                       source_text_cn: str = "") -> Tuple[str, str]:
    """
    构建词汇分解 (interlinear gloss) 的 prompt

    Returns:
        (system_prompt, user_prompt)
    """
    system_prompt = (
        "你是一位经验丰富的语言学家，擅长莱比锡标注规则 (Leipzig Glossing Rules) 的 interlinear gloss 分析。\n\n"
        "## 标注规则\n"
        "- 每个原文词对应一个 gloss 项，用空格分隔，词数必须与原文一致\n"
        "- 词素边界用连字符 - 连接（如 book-PL）\n"
        "- 语法范畴用大写缩写（如 NOM, PST, CLF）\n"
        "- 词汇义用小写英文（如 house, eat, big）\n"
        "- 零形态素不标注，隐含信息不添加额外标记\n\n"
        f"## 常用缩写\n{LEIPZIG_ABBREVIATIONS}\n\n"
        "## 输出要求\n"
        "- 只返回 gloss 行，不要添加任何解释、编号或额外文字\n"
        "- 词数必须与原文词数完全一致\n"
        "- 如果无法确定某个词的分析，使用 ??? 占位"
    )

    # 构建 user prompt
    parts = []
    context_text = _format_context_entries(context_entries)
    if context_text:
        parts.append(f"以下是该语言的已有标注示例，供你参考：\n\n{context_text}")
    parts.append("请对以下原文进行词汇分解标注：")
    parts.append(f"原文: {source_text}")
    if source_text_cn:
        parts.append(f"原文(汉字): {source_text_cn}")
    parts.append("\n请只返回 gloss 行：")

    user_prompt = "\n".join(parts)
    return system_prompt, user_prompt


def build_translation_prompt(source_text: str, gloss: str,
                             context_entries: List[Dict],
                             source_text_cn: str = "") -> Tuple[str, str]:
    """
    构建翻译 prompt

    Returns:
        (system_prompt, user_prompt)
    """
    system_prompt = (
        "你是一位语言学翻译专家，擅长将田野调查中收集的少数民族语言/方言语料翻译为准确、自然的中文。\n\n"
        "## 翻译要求\n"
        "- 翻译应忠实于原文语义，同时符合中文表达习惯\n"
        "- 参考提供的词汇分解 (gloss) 理解原文结构\n"
        "- 保持术语和专有名词的一致性\n\n"
        "## 输出要求\n"
        "- 只返回翻译结果，不要添加任何解释或额外文字"
    )

    parts = []
    context_text = _format_context_entries(context_entries)
    if context_text:
        parts.append(f"以下是该语言的已有翻译示例，供你参考：\n\n{context_text}")
    parts.append("请翻译以下语料：")
    parts.append(f"原文: {source_text}")
    if source_text_cn:
        parts.append(f"原文(汉字): {source_text_cn}")
    if gloss:
        parts.append(f"词汇分解: {gloss}")
    parts.append("\n请只返回中文翻译：")

    user_prompt = "\n".join(parts)
    return system_prompt, user_prompt
