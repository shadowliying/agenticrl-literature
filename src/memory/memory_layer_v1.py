# encoding: utf-8  # 文件编码声明
# Memory Layer（v1）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
from dataclasses import dataclass, field  # 数据类与默认工厂
from typing import Any, Dict, List, Optional  # 类型注解
import time  # 时间工具
@dataclass  # 数据类装饰器
class MemoryItem:  # 记忆条目结构
    content: str  # 记忆内容
    source: str = "unknown"  # 来源标记
    timestamp: float = field(default_factory=time.time)  # 时间戳
    tags: List[str] = field(default_factory=list)  # 标签列表
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
class MemoryLayer:  # 记忆层定义
    def __init__(self, max_short: int = 50):  # 初始化
        self.max_short = max_short  # 短期容量
        self.short_term: List[MemoryItem] = []  # 短期记忆
        self.long_term: List[MemoryItem] = []  # 长期记忆
    def write(self, content: str, scope: str = "short", source: str = "unknown", tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:  # 写入记忆
        item = MemoryItem(  # 构建记忆条目
            content=content,  # 内容
            source=source,  # 来源
            tags=tags or [],  # 标签
            metadata=metadata or {},  # 元数据
        )  # 条目构建结束
        if scope == "long":  # 判断写入长期
            self.long_term.append(item)  # 写入长期列表
        else:  # 默认写入短期
            self.short_term.append(item)  # 写入短期列表
            if len(self.short_term) > self.max_short:  # 超过容量
                self.short_term.pop(0)  # 淘汰最早条目
        return item  # 返回条目
    def recall(self, query: str, top_k: int = 5, scope: str = "all") -> List[MemoryItem]:  # 回忆记忆
        query_lower = query.lower()  # 统一小写
        candidates: List[MemoryItem] = []  # 候选列表
        if scope in ("short", "all"):  # 短期范围
            candidates.extend(self.short_term)  # 加入短期
        if scope in ("long", "all"):  # 长期范围
            candidates.extend(self.long_term)  # 加入长期
        scored: List[tuple] = []  # 评分列表
        for item in candidates:  # 遍历候选
            score = 1.0 if query_lower in item.content.lower() else 0.0  # 关键词匹配评分
            if score > 0:  # 仅保留匹配
                scored.append((score, item))  # 记录评分
        scored.sort(key=lambda x: x[0], reverse=True)  # 按分排序
        return [it for _, it in scored[:top_k]]  # 返回TopK
    def clear_short(self) -> None:  # 清空短期
        self.short_term.clear()  # 清空短期列表
    def clear_long(self) -> None:  # 清空长期
        self.long_term.clear()  # 清空长期列表
