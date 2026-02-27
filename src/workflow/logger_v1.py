# encoding: utf-8  # 文件编码声明
# 结构化轨迹日志（v1）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
from dataclasses import dataclass, field  # 数据类
from typing import Any, Dict, List  # 类型注解
import time  # 时间模块
# 轨迹步骤  # 分隔说明
@dataclass  # 数据类装饰器
class TraceStep:  # 单步轨迹
    step_id: str  # 步骤ID
    state: str  # 当前状态
    action: str  # 动作类型
    timestamp: float = field(default_factory=time.time)  # 时间戳
    reward: float = 0.0  # 奖励值
    sufficiency_score: float = 0.0  # 充分性评分
    info_gain: float = 0.0  # 信息增益
    details: Dict[str, Any] = field(default_factory=dict)  # 额外细节
# 轨迹记录器  # 分隔说明
class TraceLogger:  # 轨迹日志类
    def __init__(self):  # 初始化
        self.steps: List[TraceStep] = []  # 轨迹列表
    def log_step(self, step: TraceStep) -> None:  # 记录单步
        self.steps.append(step)  # 添加到列表
    def export(self) -> List[Dict[str, Any]]:  # 导出为字典列表
        return [  # 返回列表
            {  # 单条记录
                "step_id": s.step_id,  # 步骤ID
                "state": s.state,  # 状态
                "action": s.action,  # 动作
                "timestamp": s.timestamp,  # 时间戳
                "reward": s.reward,  # 奖励
                "sufficiency_score": s.sufficiency_score,  # 充分性
                "info_gain": s.info_gain,  # 信息增益
                "details": dict(s.details),  # 细节
            }  # 记录结束
            for s in self.steps  # 遍历记录
        ]  # 返回结束
