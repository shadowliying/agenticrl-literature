# encoding: utf-8  # 文件编码声明
# v1 工作流工具函数  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
from typing import Any, Dict, List, Tuple  # 类型注解
# 文本归一化  # 分隔说明
def normalize_text(text: str) -> str:  # 归一化文本
    return " ".join(text.lower().split())  # 小写并压缩空白
# 去重证据  # 分隔说明
def dedupe_snippets(snippets: List[str]) -> List[str]:  # 证据去重
    seen = set()  # 已见集合
    deduped: List[str] = []  # 去重结果
    for s in snippets:  # 遍历片段
        key = normalize_text(s)  # 归一化
        if key in seen:  # 已存在
            continue  # 跳过
        seen.add(key)  # 记录
        deduped.append(s)  # 保留原文
    return deduped  # 返回去重结果
# 计算信息增益  # 分隔说明
def calc_info_gain(current_snippets: List[str], previous_snippets: List[str]) -> float:  # 信息增益
    if not current_snippets:  # 空列表
        return 0.0  # 无增益
    prev_set = set(normalize_text(s) for s in previous_snippets)  # 之前片段集合
    new_count = 0  # 新片段数量
    for s in current_snippets:  # 遍历当前片段
        if normalize_text(s) not in prev_set:  # 新片段
            new_count += 1  # 计数
    return new_count / max(1, len(current_snippets))  # 归一化
# 构建证据映射  # 分隔说明
def build_evidence_mapping(snippets: List[str], slots: List[str]) -> Dict[str, List[str]]:  # 证据映射
    mapping: Dict[str, List[str]] = {slot: [] for slot in slots}  # 初始化映射
    for s in snippets:  # 遍历片段
        for slot in slots:  # 遍历槽位
            if slot and slot in s:  # 简单匹配
                mapping[slot].append(s)  # 记录片段
    return mapping  # 返回映射
# 证据摘要  # 分隔说明
def summarize_evidence(snippets: List[str], max_items: int = 5) -> List[str]:  # 摘要证据
    return snippets[:max_items]  # 简单截断
# 统计重复率  # 分隔说明
def calc_dup_ratio(snippets: List[str]) -> float:  # 重复率
    if not snippets:  # 空列表
        return 0.0  # 返回0
    normed = [normalize_text(s) for s in snippets]  # 归一化列表
    unique = len(set(normed))  # 唯一数量
    return 1.0 - (unique / max(1, len(normed)))  # 重复比例
