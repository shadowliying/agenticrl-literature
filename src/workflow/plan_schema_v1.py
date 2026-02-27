# encoding: utf-8  # 文件编码声明
# 结构化计划Schema（v1）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
# 以上为编码与前向引用设置  # 分隔说明
from dataclasses import dataclass, field  # 数据类与默认工厂
from typing import Any, Dict, List, Optional  # 类型注解
# 以上为类型与数据类导入  # 分隔说明
@dataclass  # 数据类装饰器
class PlanStep:  # 单个计划步骤结构
    step_id: str  # 步骤ID
    title: str  # 步骤标题
    action: str  # 动作类型
    description: str = ""  # 步骤描述
    inputs: List[str] = field(default_factory=list)  # 输入列表
    outputs: List[str] = field(default_factory=list)  # 输出列表
    success_criteria: List[str] = field(default_factory=list)  # 成功条件（人类可读）
    success_rules: List[Dict[str, Any]] = field(default_factory=list)  # 成功规则（机器可执行）
    dependencies: List[str] = field(default_factory=list)  # 依赖步骤ID列表
    rollback_conditions: List[str] = field(default_factory=list)  # 回退条件（人类可读）
    rollback_rules: List[Dict[str, Any]] = field(default_factory=list)  # 回退规则（机器可执行）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    def to_dict(self) -> Dict[str, Any]:  # 转为字典
        return {  # 返回结构化字典
            "step_id": self.step_id,  # 步骤ID
            "title": self.title,  # 步骤标题
            "action": self.action,  # 动作类型
            "description": self.description,  # 步骤描述
            "inputs": list(self.inputs),  # 输入列表
            "outputs": list(self.outputs),  # 输出列表
            "success_criteria": list(self.success_criteria),  # 成功条件
            "success_rules": list(self.success_rules),  # 成功规则
            "dependencies": list(self.dependencies),  # 依赖步骤ID列表
            "rollback_conditions": list(self.rollback_conditions),  # 回退条件
            "rollback_rules": list(self.rollback_rules),  # 回退规则
            "metadata": dict(self.metadata),  # 额外元数据
        }  # 字典结束
    @classmethod  # 类方法装饰器
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":  # 从字典构建
        return cls(  # 构造PlanStep
            step_id=str(data.get("step_id", "")),  # 读取步骤ID
            title=str(data.get("title", "")),  # 读取步骤标题
            action=str(data.get("action", "")),  # 读取动作类型
            description=str(data.get("description", "")),  # 读取描述
            inputs=list(data.get("inputs", [])),  # 读取输入
            outputs=list(data.get("outputs", [])),  # 读取输出
            success_criteria=list(data.get("success_criteria", [])),  # 读取成功条件
            success_rules=list(data.get("success_rules", [])),  # 读取成功规则
            dependencies=list(data.get("dependencies", [])),  # 读取依赖
            rollback_conditions=list(data.get("rollback_conditions", [])),  # 读取回退条件
            rollback_rules=list(data.get("rollback_rules", [])),  # 读取回退规则
            metadata=dict(data.get("metadata", {})),  # 读取元数据
        )  # 构造结束
# 以上为PlanStep定义  # 分隔说明
@dataclass  # 数据类装饰器
class Plan:  # 结构化计划
    goal: str  # 计划目标
    steps: List[PlanStep]  # 计划步骤列表
    constraints: List[str] = field(default_factory=list)  # 约束条件
    assumptions: List[str] = field(default_factory=list)  # 假设条件
    created_at: Optional[str] = None  # 创建时间（可选）
    version: str = "v1"  # 版本号
    def to_dict(self) -> Dict[str, Any]:  # 转为字典
        return {  # 返回结构化字典
            "goal": self.goal,  # 目标
            "steps": [s.to_dict() for s in self.steps],  # 步骤列表
            "constraints": list(self.constraints),  # 约束条件
            "assumptions": list(self.assumptions),  # 假设条件
            "created_at": self.created_at,  # 创建时间
            "version": self.version,  # 版本号
        }  # 字典结束
    @classmethod  # 类方法装饰器
    def from_dict(cls, data: Dict[str, Any]) -> "Plan":  # 从字典构建
        return cls(  # 构造Plan
            goal=str(data.get("goal", "")),  # 读取目标
            steps=[PlanStep.from_dict(s) for s in data.get("steps", [])],  # 读取步骤
            constraints=list(data.get("constraints", [])),  # 读取约束
            assumptions=list(data.get("assumptions", [])),  # 读取假设
            created_at=data.get("created_at"),  # 读取创建时间
            version=str(data.get("version", "v1")),  # 读取版本
        )  # 构造结束
# 以上为Plan定义  # 分隔说明
def validate_plan(plan: Plan) -> List[str]:  # 轻量校验函数
    errors: List[str] = []  # 错误列表
    if not plan.goal:  # 目标不能为空
        errors.append("plan.goal is required")  # 添加错误
    step_ids = [s.step_id for s in plan.steps]  # 收集所有步骤ID
    if not step_ids:  # 步骤不能为空
        errors.append("plan.steps must not be empty")  # 添加错误
    if len(step_ids) != len(set(step_ids)):  # 检查重复ID
        errors.append("plan.steps contains duplicate step_id values")  # 添加错误
    for step in plan.steps:  # 遍历步骤
        if not step.step_id:  # step_id不能为空
            errors.append("plan.steps has a step with empty step_id")  # 添加错误
        if not step.title:  # 标题不能为空
            errors.append(f"step '{step.step_id}' is missing title")  # 添加错误
        if not step.action:  # 动作不能为空
            errors.append(f"step '{step.step_id}' is missing action")  # 添加错误
    return errors  # 返回错误列表
# 以上为校验函数  # 分隔说明
def example_plan() -> Plan:  # 提供最小示例
    steps = [  # 构建步骤列表
        PlanStep(  # 第一步
            step_id="S1",  # 步骤ID
            title="Retrieve evidence",  # 步骤标题
            action="RETRIEVE",  # 动作类型
            description="Search and collect evidence snippets.",  # 步骤描述
            outputs=["evidence_snippets"],  # 产出字段
            success_criteria=["至少 2 条证据"],  # 成功条件（人类可读）
            success_rules=[{"type": "min_snippets", "value": 2}],  # 成功规则（机器可执行）
        ),  # 第一步结束
        PlanStep(  # 第二步
            step_id="S2",  # 步骤ID
            title="Validate sufficiency",  # 步骤标题
            action="VALIDATE",  # 动作类型
            description="Score evidence coverage and consistency.",  # 步骤描述
            inputs=["evidence_snippets"],  # 输入字段
            outputs=["sufficiency_score", "missing_slots"],  # 产出字段
            dependencies=["S1"],  # 依赖步骤
            success_criteria=["sufficiency_score >= 0.75"],  # 成功条件
            success_rules=[{"type": "sufficiency_score_ge", "value": 0.75}],  # 成功规则
            rollback_conditions=["sufficiency_score < 0.60"],  # 回退条件
            rollback_rules=[{"type": "sufficiency_score_lt", "value": 0.60}],  # 回退规则
            metadata={  # 额外元数据
                "required_slots": ["time", "number", "comparison"],  # 必须覆盖槽位
                "sufficiency_threshold": 0.75,  # 充分阈值
                "replan_threshold": 0.60,  # 重规划阈值
                "min_snippets": 2,  # 最少证据数
            },  # 元数据结束
        ),  # 第二步结束
        PlanStep(  # 第三步
            step_id="S3",  # 步骤ID
            title="Synthesize answer",  # 步骤标题
            action="SYNTHESIS",  # 动作类型
            description="Write the final answer using validated evidence.",  # 步骤描述
            inputs=["evidence_snippets", "sufficiency_score"],  # 输入字段
            outputs=["final_answer"],  # 产出字段
            dependencies=["S2"],  # 依赖步骤
            success_criteria=["回答包含关键槽位"],  # 成功条件
            success_rules=[],  # 成功规则（此处留空）
        ),  # 第三步结束
    ]  # 步骤列表结束
    return Plan(  # 构建Plan
        goal="Answer the user question with verified evidence.",  # 计划目标
        steps=steps,  # 步骤列表
        constraints=["avoid unsupported claims"],  # 约束条件
        assumptions=["search tools available"],  # 假设条件
        created_at=None,  # 创建时间
        version="v1",  # 版本号
    )  # Plan构建结束
