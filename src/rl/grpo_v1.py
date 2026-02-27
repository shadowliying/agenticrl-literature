# encoding: utf-8  # 文件编码声明
# GRPO 奖励与两段式切换（v1）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
from dataclasses import dataclass  # 数据类
from typing import Dict  # 类型注解
# 阶段权重配置  # 分隔说明
@dataclass  # 数据类装饰器
class RewardWeights:  # 奖励权重结构
    r_quality: float  # 终局质量
    r_sufficiency: float  # 充分性
    r_info_gain: float  # 信息增益
    r_efficiency: float  # 效率
# 两段式权重  # 分隔说明
PHASE1_WEIGHTS = RewardWeights(  # 阶段一权重
    r_quality=0.25,  # 终局质量权重
    r_sufficiency=0.35,  # 充分性权重
    r_info_gain=0.25,  # 信息增益权重
    r_efficiency=0.15,  # 效率权重
)  # 阶段一结束
PHASE2_WEIGHTS = RewardWeights(  # 阶段二权重
    r_quality=0.40,  # 终局质量权重
    r_sufficiency=0.25,  # 充分性权重
    r_info_gain=0.20,  # 信息增益权重
    r_efficiency=0.15,  # 效率权重
)  # 阶段二结束
# 计算奖励  # 分隔说明
def compute_reward(  # 奖励计算函数
    weights: RewardWeights,  # 权重
    r_quality: float,  # 终局质量
    r_sufficiency: float,  # 充分性
    r_info_gain: float,  # 信息增益
    r_efficiency: float,  # 效率
    r_penalty: float = 0.0,  # 惩罚项
) -> float:  # 返回总奖励
    return (  # 总奖励
        weights.r_quality * r_quality  # 终局质量
        + weights.r_sufficiency * r_sufficiency  # 充分性
        + weights.r_info_gain * r_info_gain  # 信息增益
        + weights.r_efficiency * r_efficiency  # 效率
        - r_penalty  # 惩罚
    )  # 计算结束
# 切换阶段  # 分隔说明
def select_phase(step: int, total_steps: int, sufficiency_avg: float = 0.0, info_gain_avg: float = 0.0) -> Dict[str, float]:  # 选择阶段
    if total_steps <= 0:  # 防御
        return PHASE1_WEIGHTS.__dict__  # 默认阶段一
    ratio = step / total_steps  # 训练比例
    if ratio >= 0.6:  # 达到 60% 进入阶段二
        return PHASE2_WEIGHTS.__dict__  # 返回阶段二
    if sufficiency_avg >= 0.75 and info_gain_avg >= 0.5:  # 指标稳定
        return PHASE2_WEIGHTS.__dict__  # 切换阶段二
    return PHASE1_WEIGHTS.__dict__  # 仍为阶段一
