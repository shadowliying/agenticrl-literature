# encoding: utf-8  # 文件编码声明
# 状态机执行定义（v1）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
# 导入依赖  # 分隔说明
from dataclasses import dataclass  # 数据类
from enum import Enum  # 枚举类型
from typing import Any, Dict, Optional, Tuple  # 类型注解
# 导入计划结构  # 分隔说明
from .plan_schema_v1 import Plan  # 引入Plan类型
# 定义状态枚举  # 分隔说明
class State(Enum):  # 状态枚举类
    PLAN = "PLAN"  # 计划阶段
    RETRIEVE = "RETRIEVE"  # 检索阶段
    VALIDATE = "VALIDATE"  # 验证阶段
    REPLAN = "REPLAN"  # 重规划阶段
    SYNTHESIS = "SYNTHESIS"  # 合成阶段
    ANSWER = "ANSWER"  # 输出阶段
    END = "END"  # 终止阶段
# 定义转移结果  # 分隔说明
@dataclass  # 数据类装饰器
class TransitionResult:  # 状态转移结果
    next_state: State  # 下一状态
    reason: str  # 转移原因
    allowed: bool = True  # 是否允许的转移
# 允许转移表  # 分隔说明
ALLOWED_TRANSITIONS: Dict[State, Tuple[State, ...]] = {  # 允许转移映射
    State.PLAN: (State.RETRIEVE,),  # 计划 -> 检索
    State.RETRIEVE: (State.VALIDATE,),  # 检索 -> 验证
    State.VALIDATE: (State.RETRIEVE, State.REPLAN, State.SYNTHESIS),  # 验证 -> 检索/重规划/合成
    State.REPLAN: (State.RETRIEVE,),  # 重规划 -> 检索
    State.SYNTHESIS: (State.ANSWER,),  # 合成 -> 输出
    State.ANSWER: (State.END,),  # 输出 -> 终止
    State.END: (State.END,),  # 终止 -> 终止
}  # 转移表结束
# 构建默认上下文  # 分隔说明
def build_default_context(plan: Optional[Plan] = None) -> Dict[str, Any]:  # 生成默认上下文
    ctx: Dict[str, Any] = {  # 初始化上下文字典
        "sufficiency_score": 0.0,  # 当前充分性评分
        "sufficiency_threshold": 0.75,  # 充分阈值
        "replan_threshold": 0.60,  # 重规划阈值
        "step_count": 0,  # 当前步数
        "max_steps": 12,  # 最大步数
        "force_replan": False,  # 是否强制重规划
        "fatal_error": False,  # 是否出现致命错误
    }  # 上下文初始化结束
    if plan is not None:  # 如果传入计划
        ctx["goal"] = plan.goal  # 写入目标信息
    return ctx  # 返回上下文
# 状态机主体  # 分隔说明
class StateMachine:  # 状态机类
    def __init__(self, sufficiency_threshold: float = 0.75, replan_threshold: float = 0.60, max_steps: int = 12):  # 初始化
        self.sufficiency_threshold = sufficiency_threshold  # 充分阈值
        self.replan_threshold = replan_threshold  # 重规划阈值
        self.max_steps = max_steps  # 最大步数
    def is_transition_allowed(self, current_state: State, next_state: State) -> bool:  # 判断转移合法性
        allowed = ALLOWED_TRANSITIONS.get(current_state, (State.END,))  # 获取允许的下一状态
        return next_state in allowed  # 返回是否允许
    def next_state(self, current_state: State, context: Optional[Dict[str, Any]] = None) -> TransitionResult:  # 计算下一状态
        if context is None:  # 如果未传入上下文
            context = {}  # 使用空上下文
        sufficiency_score = float(context.get("sufficiency_score", 0.0))  # 当前充分性
        sufficiency_threshold = float(context.get("sufficiency_threshold", self.sufficiency_threshold))  # 充分阈值
        replan_threshold = float(context.get("replan_threshold", self.replan_threshold))  # 重规划阈值
        step_count = int(context.get("step_count", 0))  # 当前步数
        max_steps = int(context.get("max_steps", self.max_steps))  # 最大步数
        force_replan = bool(context.get("force_replan", False))  # 是否强制重规划
        fatal_error = bool(context.get("fatal_error", False))  # 是否致命错误
        if fatal_error:  # 如果出现致命错误
            return TransitionResult(State.END, "fatal_error", True)  # 直接终止
        if step_count >= max_steps:  # 如果达到最大步数
            return TransitionResult(State.END, "max_steps_reached", True)  # 直接终止
        if current_state == State.PLAN:  # 当前为计划阶段
            return TransitionResult(State.RETRIEVE, "plan_ready", True)  # 转到检索
        if current_state == State.RETRIEVE:  # 当前为检索阶段
            return TransitionResult(State.VALIDATE, "retrieval_done", True)  # 转到验证
        if current_state == State.VALIDATE:  # 当前为验证阶段
            if force_replan:  # 强制重规划
                return TransitionResult(State.REPLAN, "force_replan", True)  # 转到重规划
            if sufficiency_score >= sufficiency_threshold:  # 如果充分性达标
                return TransitionResult(State.SYNTHESIS, "sufficient", True)  # 转到合成
            if sufficiency_score < replan_threshold:  # 如果充分性过低
                return TransitionResult(State.REPLAN, "insufficient_replan", True)  # 转到重规划
            return TransitionResult(State.RETRIEVE, "insufficient_retry", True)  # 返回检索
        if current_state == State.REPLAN:  # 当前为重规划阶段
            return TransitionResult(State.RETRIEVE, "replan_done", True)  # 转到检索
        if current_state == State.SYNTHESIS:  # 当前为合成阶段
            return TransitionResult(State.ANSWER, "synthesis_done", True)  # 转到输出
        if current_state == State.ANSWER:  # 当前为输出阶段
            return TransitionResult(State.END, "answer_done", True)  # 转到终止
        return TransitionResult(State.END, "unknown_state", False)  # 兜底终止
