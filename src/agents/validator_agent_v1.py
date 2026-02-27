# encoding: utf-8  # 文件编码声明
# Validator Agent（v1，规则评分版）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
import re  # 正则模块
from typing import Any, Dict, List, Optional, Tuple  # 类型注解
# 引入基础Agent  # 分隔说明
from .base_agent_v1 import BaseAgentV1  # 引入基础Agent
# 引入提示词  # 分隔说明
from .prompts.validator_agent_prompts_v1 import SYSTEM_PROMPT  # 系统提示词
# 停用词列表  # 分隔说明
STOPWORDS = ["什么", "多少", "如何", "怎么", "请问", "是否", "可以", "这", "那", "以及", "包含", "比较", "对比", "增长", "下降"]  # 简单停用词
# 槽位关键词规则  # 分隔说明
SLOT_KEYWORDS = {  # 槽位关键词映射
    "time": ["时间", "日期", "哪年", "何时", "去年", "今年", "当年", "year", "when"],  # 时间关键词
    "number": ["多少", "数量", "比例", "%", "增长", "下降", "rate", "percent", "how many"],  # 数量关键词
    "comparison": ["同比", "环比", "对比", "比较", "差异", "increase", "decrease", "vs"],  # 对比关键词
    "reason": ["原因", "为什么", "导致", "why", "reason"],  # 原因关键词
    "method": ["如何", "怎么", "方法", "过程", "步骤", "how to", "method"],  # 方法关键词
    "definition": ["是什么", "定义", "含义", "meaning", "definition"],  # 定义关键词
}  # 规则结束
# 文本归一化  # 分隔说明
def _normalize_text(text: str) -> str:  # 归一化文本
    return "".join(text.lower().split())  # 小写并去空白
# 关键词抽取  # 分隔说明
def _extract_tokens(text: str) -> List[str]:  # 提取关键词
    tokens: List[str] = []  # 初始化列表
    buf: str = ""  # 缓冲区
    for ch in text:  # 遍历字符
        if ch.isalnum():  # 字母数字
            buf += ch  # 拼接缓冲区
        else:  # 非字母数字
            if buf:  # 缓冲区非空
                tokens.append(buf)  # 追加token
                buf = ""  # 清空缓冲区
            if "\u4e00" <= ch <= "\u9fff":  # 中文字符
                tokens.append(ch)  # 追加单字
    if buf:  # 处理尾部
        tokens.append(buf)  # 追加剩余
    return tokens  # 返回token列表
# 实体抽取（规则）  # 分隔说明
def _extract_entities(text: str) -> List[str]:  # 抽取实体
    entities: List[str] = []  # 初始化列表
    cn_chunks = re.findall(r"[\u4e00-\u9fff]{2,6}", text)  # 抽取中文片段
    en_chunks = re.findall(r"[A-Z][A-Za-z0-9\-]{1,20}", text)  # 抽取英文片段
    for c in cn_chunks:  # 遍历中文片段
        if c not in STOPWORDS:  # 过滤停用词
            entities.append(c)  # 追加实体
    for e in en_chunks:  # 遍历英文片段
        entities.append(e)  # 追加实体
    return list(dict.fromkeys(entities))  # 去重返回
# 推断槽位（规则）  # 分隔说明
def _infer_slots(question: str, entities: List[str]) -> List[str]:  # 推断槽位
    slots: List[str] = []  # 初始化槽位
    for slot, keys in SLOT_KEYWORDS.items():  # 遍历槽位规则
        if any(k in question for k in keys):  # 命中关键词
            slots.append(slot)  # 添加槽位
    if entities:  # 若有实体
        slots.append("entity")  # 添加实体槽位
    return list(dict.fromkeys(slots))  # 去重返回
# 槽位覆盖判断  # 分隔说明
def _slot_covered(slot: str, evidence_text: str, entities: List[str]) -> bool:  # 判断槽位覆盖
    text = evidence_text  # 证据文本
    if slot == "time":  # 时间槽位
        if re.search(r"\b(19|20)\d{2}\b", text):  # 年份匹配
            return True  # 命中
        return any(k in text for k in ["年", "月", "日", "时间", "日期", "year", "month", "day"])  # 关键词匹配
    if slot == "number":  # 数量槽位
        if re.search(r"\d", text):  # 数字匹配
            return True  # 命中
        return any(k in text for k in ["%", "万", "亿", "比例", "rate", "percent", "number"])  # 关键词匹配
    if slot == "comparison":  # 对比槽位
        return any(k in text for k in ["同比", "环比", "对比", "比较", "差异", "increase", "decrease", "vs"])  # 关键词匹配
    if slot == "reason":  # 原因槽位
        return any(k in text for k in ["原因", "因为", "导致", "why", "reason"])  # 关键词匹配
    if slot == "method":  # 方法槽位
        return any(k in text for k in ["方法", "步骤", "流程", "how", "method"])  # 关键词匹配
    if slot == "definition":  # 定义槽位
        return any(k in text for k in ["是指", "定义", "含义", "meaning", "definition"])  # 关键词匹配
    if slot == "entity":  # 实体槽位
        return any(e and e in text for e in entities)  # 实体匹配
    return False  # 默认未命中
# 相关性评分  # 分隔说明
def _score_relevance(question_tokens: List[str], evidence_snippets: List[str]) -> float:  # 相关性评分
    if not evidence_snippets:  # 无证据
        return 0.0  # 返回0
    matched = 0  # 命中计数
    for snip in evidence_snippets:  # 遍历片段
        if any(t and t in snip for t in question_tokens):  # 命中任一token
            matched += 1  # 计数增加
    return matched / max(1, len(evidence_snippets))  # 归一化
# 支持强度评分  # 分隔说明
def _score_support_strength(evidence_snippets: List[str]) -> float:  # 支持强度评分
    if not evidence_snippets:  # 无证据
        return 0.0  # 返回0
    total_len = sum(len(s) for s in evidence_snippets)  # 总长度
    avg_len = total_len / max(1, len(evidence_snippets))  # 平均长度
    has_number = any(any(ch.isdigit() for ch in s) for s in evidence_snippets)  # 数字存在
    base = min(1.0, avg_len / 200.0)  # 基础分
    if has_number:  # 若有数字
        base = min(1.0, base + 0.2)  # 加分
    return base  # 返回分数
# 信息增益评分  # 分隔说明
def _score_info_gain(evidence_snippets: List[str], previous_snippets: List[str]) -> float:  # 信息增益评分
    if not evidence_snippets:  # 无证据
        return 0.0  # 返回0
    prev_set = set(_normalize_text(s) for s in (previous_snippets or []))  # 历史片段集合
    new_count = sum(1 for s in evidence_snippets if _normalize_text(s) not in prev_set)  # 新片段数量
    return new_count / max(1, len(evidence_snippets))  # 归一化
# 一致性评分  # 分隔说明
def _score_consistency(conflicts: List[str], evidence_snippets: List[str]) -> Tuple[float, float]:  # 一致性与冲突比
    conflict_ratio = min(1.0, len(conflicts) / max(1, len(evidence_snippets)))  # 冲突比例
    consistency = 1.0 - conflict_ratio  # 一致性分
    return consistency, conflict_ratio  # 返回一致性与冲突比
# Validator Agent 定义  # 分隔说明
class ValidatorAgentV1(BaseAgentV1):  # 验证Agent v1
    def __init__(self, llm: Optional[Any] = None):  # 初始化
        self.llm = llm  # 预留LLM接口（规则版不使用）
        self.system_prompt = SYSTEM_PROMPT  # 系统提示词
    def run(self, evidence_snippets: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:  # 执行验证
        ctx = context or {}  # 兼容上下文
        question = str(ctx.get("question", ""))  # 读取问题
        plan_rules: Dict[str, Any] = dict(ctx.get("plan_rules", {}))  # 读取计划规则
        entities = _extract_entities(question)  # 抽取实体
        required_slots: List[str] = list(ctx.get("required_slots", []))  # 读取槽位
        if (not required_slots) and plan_rules.get("required_slots"):  # 计划规则提供槽位
            required_slots = list(plan_rules.get("required_slots", []))  # 使用计划规则
        if not required_slots:  # 若未提供槽位
            required_slots = _infer_slots(question, entities)  # 规则推断槽位
        min_snippets = int(plan_rules.get("min_snippets", 0))  # 最少证据数
        evidence_text = "\n".join(evidence_snippets)  # 合并证据文本
        missing_slots: List[str] = []  # 缺失槽位
        for slot in required_slots:  # 遍历槽位
            if not _slot_covered(slot, evidence_text, entities):  # 若未覆盖
                missing_slots.append(slot)  # 记录缺失
        coverage = 1.0  # 默认覆盖度
        if required_slots:  # 若存在槽位
            coverage = 1.0 - (len(missing_slots) / max(1, len(required_slots)))  # 计算覆盖度
        question_tokens = _extract_tokens(question)  # 提取问题token
        relevance = _score_relevance(question_tokens, evidence_snippets)  # 相关性
        support_strength = _score_support_strength(evidence_snippets)  # 支持强度
        previous_snippets: List[str] = list(ctx.get("previous_snippets", []))  # 历史片段
        info_gain = _score_info_gain(evidence_snippets, previous_snippets)  # 信息增益
        conflicts: List[str] = list(ctx.get("conflicts", []))  # 冲突列表
        consistency, conflict_ratio = _score_consistency(conflicts, evidence_snippets)  # 一致性
        source_quality_scores: List[float] = list(ctx.get("source_quality_scores", []))  # 来源评分
        source_quality = (sum(source_quality_scores) / max(1, len(source_quality_scores))) if source_quality_scores else (0.5 if evidence_snippets else 0.0)  # 来源质量
        freshness_scores: List[float] = list(ctx.get("freshness_scores", []))  # 时效评分
        freshness = (sum(freshness_scores) / max(1, len(freshness_scores))) if freshness_scores else (0.5 if evidence_snippets else 0.0)  # 时效性
        sufficiency_score = (  # 综合评分
            0.35 * coverage  # 覆盖度权重
            + 0.20 * relevance  # 相关性权重
            + 0.15 * support_strength  # 支持强度权重
            + 0.10 * consistency  # 一致性权重
            + 0.10 * source_quality  # 来源权重
            + 0.05 * freshness  # 时效权重
            + 0.05 * info_gain  # 增益权重
        )  # 评分结束
        high_risk = bool(ctx.get("high_risk", False))  # 高风险问题
        time_sensitive = bool(ctx.get("time_sensitive", False))  # 时间敏感
        hard_block = False  # 硬性门槛
        if missing_slots:  # 关键槽位缺失
            hard_block = True  # 触发门槛
        if conflict_ratio > 0.4:  # 冲突过高
            hard_block = True  # 触发门槛
        if min_snippets > 0 and len(evidence_snippets) < min_snippets:  # 证据数不足
            hard_block = True  # 触发门槛
        if high_risk and source_quality < 0.4:  # 高风险且来源差
            hard_block = True  # 触发门槛
        if time_sensitive and freshness < 0.4:  # 时间敏感但不新
            hard_block = True  # 触发门槛
        sufficiency_threshold = float(plan_rules.get("sufficiency_threshold", ctx.get("sufficiency_threshold", 0.75)))  # 充分阈值
        is_sufficient = (sufficiency_score >= sufficiency_threshold) and (not hard_block)  # 是否充分
        if is_sufficient:  # 若充分
            suggested_action = "synthesize"  # 建议合成
        elif conflict_ratio > 0.4:  # 冲突高
            suggested_action = "replan"  # 建议重规划
        else:  # 默认情况
            suggested_action = "search_more"  # 继续检索
        return {  # 返回结构化结果
            "sufficiency": is_sufficient,  # 是否充分
            "sufficiency_score": round(sufficiency_score, 4),  # 充分性评分
            "coverage": round(coverage, 4),  # 覆盖度
            "relevance": round(relevance, 4),  # 相关性
            "support_strength": round(support_strength, 4),  # 支持强度
            "consistency": round(consistency, 4),  # 一致性
            "info_gain": round(info_gain, 4),  # 信息增益
            "source_quality": round(source_quality, 4),  # 来源质量
            "freshness": round(freshness, 4),  # 时效性
            "missing_slots": missing_slots,  # 缺失槽位
            "conflicts": conflicts,  # 冲突列表
            "suggested_action": suggested_action,  # 建议动作
        }  # 返回结束
