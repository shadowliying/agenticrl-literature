# encoding: utf-8  # 文件编码声明
# Orchestrator Agent（v1）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
from typing import Any, Dict, Optional  # 类型注解
# 引入基础与计划结构  # 分隔说明
from .base_agent_v1 import BaseAgentV1  # 引入基础Agent
from workflow.plan_schema_v1 import Plan, example_plan  # 引入计划结构
# 引入提示词  # 分隔说明
from .prompts.orchestrator_agent_prompts_v1 import SYSTEM_PROMPT  # 系统提示词
# Orchestrator Agent 定义  # 分隔说明
class OrchestratorAgentV1(BaseAgentV1):  # Orchestrator v1
    def __init__(self, llm: Optional[Any] = None):  # 初始化
        self.llm = llm  # 预留LLM接口
        self.system_prompt = SYSTEM_PROMPT  # 系统提示词
    def run(self, question: str, context: Optional[Dict[str, Any]] = None) -> Plan:  # 生成计划
        _ = context or {}  # 兼容上下文
        plan = example_plan()  # 使用示例计划作为模板
        plan.goal = question  # 将问题写入目标
        return plan  # 返回结构化计划
