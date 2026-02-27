# encoding: utf-8  # 文件编码声明
# 结构化流程执行（v1）  # 文件用途说明
from __future__ import annotations  # 允许类型前向引用
# 导入类型与依赖  # 分隔说明
from typing import Any, Callable, Dict, Optional  # 类型注解
# 导入计划与状态机  # 分隔说明
from .plan_schema_v1 import Plan, example_plan, validate_plan  # 引入计划结构
from .state_machine_v1 import State, StateMachine, build_default_context  # 引入状态机
# 导入记忆层  # 分隔说明
from memory.memory_layer_v1 import MemoryLayer  # 引入记忆层
# Handler 类型  # 分隔说明
Handler = Callable[[Dict[str, Any]], Dict[str, Any]]  # 处理函数类型

# 构建默认处理器  # 分隔说明
def default_handlers() -> Dict[State, Handler]:  # 默认处理器集合
    return {}  # 默认无处理器

# 执行主流程  # 分隔说明
def run_v1(  # 主入口函数
    question: str,  # 用户问题
    plan: Optional[Plan] = None,  # 可选计划
    handlers: Optional[Dict[State, Handler]] = None,  # 可选处理器
    memory_layer: Optional[MemoryLayer] = None,  # 可选记忆层
) -> Dict[str, Any]:  # 返回执行结果
    plan_obj = plan or example_plan()  # 使用默认计划
    errors = validate_plan(plan_obj)  # 校验计划
    if errors:  # 如果计划不合法
        return {"status": "invalid_plan", "errors": errors}  # 返回错误
    sm = StateMachine()  # 初始化状态机
    context = build_default_context(plan_obj)  # 初始化上下文
    context["question"] = question  # 写入问题
    handlers_map = handlers or default_handlers()  # 处理器映射
    memory = memory_layer or MemoryLayer()  # 记忆层实例
    state = State.PLAN  # 初始状态
    trace: list = []  # 轨迹列表
    while state != State.END:  # 循环执行
        context["step_count"] = int(context.get("step_count", 0)) + 1  # 步数递增
        if state == State.PLAN:  # 计划阶段
            recalled = memory.recall(question, top_k=5, scope="all")  # 回忆记忆
            context["memory_recall"] = [m.content for m in recalled]  # 写入回忆内容
        handler = handlers_map.get(state)  # 获取处理器
        if handler:  # 如果存在处理器
            result = handler(context)  # 执行处理器
            if isinstance(result, dict):  # 如果返回字典
                context.update(result)  # 合并上下文
        if state == State.ANSWER:  # 输出阶段
            final_answer = str(context.get("final_answer", ""))  # 获取最终答案
            if final_answer:  # 如果存在答案
                memory.write(final_answer, scope="long", source="answer")  # 写入长期记忆
        trace.append(  # 记录轨迹
            {  # 轨迹条目
                "state": state.value,  # 当前状态
                "step": context.get("step_count"),  # 当前步数
                "sufficiency_score": context.get("sufficiency_score", 0.0),  # 充分性
            }  # 轨迹结束
        )  # 记录结束
        transition = sm.next_state(state, context)  # 计算下一状态
        context["last_transition_reason"] = transition.reason  # 记录转移原因
        state = transition.next_state  # 更新状态
    return {  # 返回执行结果
        "status": "ok",  # 状态码
        "final_state": State.END.value,  # 最终状态
        "trace": trace,  # 执行轨迹
        "context": context,  # 最终上下文
    }  # 返回结束
