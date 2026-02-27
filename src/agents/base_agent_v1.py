# encoding: utf-8  # 文件编码声明
# v1 基础 Agent 抽象类  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
from abc import ABC, abstractmethod  # 抽象基类工具
# 以上为导入  # 分隔说明
class BaseAgentV1(ABC):  # v1 基础 Agent
    @abstractmethod  # 抽象方法装饰器
    def run(self, *args, **kwargs):  # 统一运行入口
        raise NotImplementedError("BaseAgentV1.run must be implemented")  # 强制子类实现
