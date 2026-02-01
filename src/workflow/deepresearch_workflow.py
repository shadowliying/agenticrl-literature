# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理和显示

import time
# 导入time模块，用于时间相关操作
# 主要用于计算代码执行耗时、延迟等功能

import json
# 导入json模块，用于JSON数据的序列化和反序列化
# 在工作流中用于保存元数据、处理API响应等

import re
# 导入re模块，提供正则表达式功能
# 用于字符串模式匹配，如提取索引号等文本处理操作

import traceback
# 导入traceback模块，用于异常追踪和错误信息获取
# 当工作流发生异常时，能够打印详细的错误堆栈信息

from agents import OrchestratorAgent, OptimizerAgent, SelectorAgent, SufficiencyValidatorAgent, ReorchestratorAgent, AssitantAgent, CodeAgent
# 从agents包导入所有智能体类
# OrchestratorAgent: 编排智能体，负责任务分解和路径规划
# OptimizerAgent: 优化智能体，负责搜索流程的优化
# SelectorAgent: 选择智能体，负责筛选相关网页内容
# SufficiencyValidatorAgent: 充分性验证智能体，判断信息是否足够
# ReorchestratorAgent: 重新编排智能体，根据当前状态重新规划路径
# AssitantAgent: 助手智能体，负责最终答案的生成
# CodeAgent: 代码智能体，负责生成和解释代码

from tools.executors import CodeExecutor
# 从工具执行器包导入代码执行器
# CodeExecutor用于执行Python代码并获取执行结果

from llms import LLMFactory
# 导入大语言模型工厂类
# 用于根据配置创建不同类型的LLM实例

from utils.common_utils import latex_render, replace_ref_tag2md, get_location_by_ip, get_real_time_str
# 从通用工具包导入实用函数
# latex_render: 处理LaTeX格式文本
# replace_ref_tag2md: 将引用标记转换为Markdown链接
# get_location_by_ip: 获取IP对应的地理位置信息
# get_real_time_str: 获取当前时间的格式化字符串

from utils.logger import model_logger
# 导入模型日志记录器
# 用于记录工作流执行过程中的关键信息和性能数据

import uuid
# 导入uuid模块，用于生成唯一标识符
# 为每个请求生成唯一的request_id，便于追踪和调试

from .utils import run_code, fetch_search_result
# 从当前包的utils模块导入代码执行和搜索结果获取函数
# run_code: 执行代码生成和运行的完整流程
# fetch_search_result: 获取搜索引擎的搜索结果

from .utils import function_call_receive_code_results, step_by_step_process, process_message
# 导入更多工作流工具函数
# function_call_receive_code_results: 处理代码执行结果的函数调用
# step_by_step_process: 将搜索流程转换为分步执行的结构
# process_message: 处理消息格式化

from .utils import function_call_receive_document, function_call_receive_snippet, function_call_sent, generate_call_id, get_tool_list, remove_ref_tag, update_search_res
# 导入更多辅助函数
# function_call_receive_document: 处理网页文档内容的函数调用
# function_call_receive_snippet: 处理网页摘要的函数调用
# function_call_sent: 发送函数调用请求
# generate_call_id: 生成函数调用的唯一ID
# get_tool_list: 获取已使用工具的列表
# remove_ref_tag: 移除文本中的引用标记
# update_search_res: 更新搜索结果

from .utils import convert_think_message_to_markdown, format_data
# 导入格式化相关函数
# convert_think_message_to_markdown: 将思考过程转换为Markdown格式
# format_data: 格式化数据用于API传输

from config import LANGUAGE, SEARCH_ENGINE, LLM_MODEL
# 从配置文件导入全局配置常量
# LANGUAGE: 系统使用的语言设置（中文/英文）
# SEARCH_ENGINE: 搜索引擎类型配置
# LLM_MODEL: 使用的大语言模型类型

def run(question, queue, api_queue, lang, context=dict(), save_jsonl_path="", debug_verbose=True, meta_verbose=False):
    # 定义主运行函数，作为工作流的入口点
    # question: 用户提出的问题
    # queue: 用于向前端传递进度信息的消息队列
    # api_queue: 用于API响应的消息队列
    # lang: 语言设置
    # context: 上下文字典，包含会话历史和状态信息
    # save_jsonl_path: 保存结果的JSONL文件路径
    # debug_verbose: 是否开启详细调试信息
    # meta_verbose: 是否开启元数据详细输出
    
    try:
        # 使用try-except包装，确保异常能够被正确处理
        run_throw_exception(question, queue, api_queue, lang, context=context, save_jsonl_path=save_jsonl_path,  debug_verbose=debug_verbose, meta_verbose=meta_verbose)
        # 调用实际的工作流执行函数
        # 将所有参数传递给具体的实现函数
    except Exception as e:
        # 捕获任何异常
        traceback.print_exc()
        # traceback 是 Python 标准库模块，用来获取和打印异常的完整堆栈信息。
        # 打印完整的异常堆栈信息，便于调试
        queue.put(["exception", None])
        # 向消息队列发送异常信号，通知前端发生错误
        api_queue.put("exception")
        # 向API队列发送异常信号
    return
    # 函数执行完毕返回

def run_throw_exception(question, queue, api_queue, lang, context=dict(), save_jsonl_path="", debug_verbose=True, meta_verbose=False):
    # 定义实际执行工作流的函数，允许异常向上传播
    # 参数含义与run函数相同，但不处理异常
    
    llm = LLMFactory.construct(LLM_MODEL)
    # 使用工厂模式创建大语言模型实例
    # 根据配置中的LLM_MODEL创建对应的模型对象
    
    orchestrator = OrchestratorAgent(llm=llm, lang=lang)
    # 创建编排智能体实例
    # 传入LLM实例和语言设置，用于任务分解和路径规划
    
    optimizer = OptimizerAgent(llm=llm, lang=lang)
    # 创建优化智能体实例
    # 用于优化搜索流程，提高搜索效率和准确性
    
    selector = SelectorAgent(llm=llm, lang=lang)
    # 创建选择智能体实例
    # 用于从搜索结果中筛选相关的网页内容
    
    validator = SufficiencyValidatorAgent(llm=llm, lang=lang)
    # 创建充分性验证智能体实例
    # 用于判断当前获取的信息是否足够回答问题
    
    reorchestrator = ReorchestratorAgent(llm=llm, lang=lang)
    # 创建重新编排智能体实例
    # 根据当前获得的信息重新规划后续的搜索路径
    
    assitant = AssitantAgent(llm=llm, lang=lang)
    # 创建助手智能体实例
    # 用于基于收集到的所有信息生成最终答案
    
    code_agent = CodeAgent(llm=llm, lang=lang)
    # 创建代码智能体实例
    # 用于生成和解释Python代码

    code_executor = CodeExecutor()
    # 创建代码执行器实例
    # 用于实际执行生成的Python代码并获取结果

    request_id = str(uuid.uuid4())
    # 生成唯一的请求ID
    # 用于标识和追踪当前请求的整个生命周期
    
    now_messages = []
    # 初始化消息列表
    # 用于存储整个对话过程中的所有消息记录
    
    meta_data = {
        "time_stamp":f"{get_real_time_str()}",
        "question": context['question'],
        "feedback": None,
        "messages" : now_messages
    }
    # 初始化元数据字典
    # time_stamp: 记录请求开始时间
    # question: 用户的原始问题
    # feedback: 用户反馈（初始为None）
    # messages: 对话消息列表的引用
    
    context["question"] = question
    # 将当前问题保存到上下文中
    # 确保在整个工作流中都能访问到原始问题
    
    queue.put(["bar", "🖥️ 智能体 · 路径规划"])
    # 向消息队列发送进度条更新信息
    # 通知前端当前正在进行路径规划阶段
    
    context["online_steps"].append("🖥️ 智能体 · 路径规划")
    # 将当前步骤添加到在线步骤列表中
    # 用于记录整个处理过程的步骤序列
    
    result = dict()
    # 初始化结果字典
    # 用于存储编排智能体的输出结果
    
    queue.put(["placeholder_begin", None])
    # 发送占位符开始信号
    # 通知前端开始显示思考过程的占位区域
    
    context["online_steps"].append("")
    # 在步骤列表中添加空字符串
    # 为即将显示的思考过程预留位置
    
    _reasoning_content = ""
    # 初始化推理内容字符串
    # 用于累积智能体的思考过程文本
    
    for label, _stream_text in orchestrator.run(question):
        # 运行编排智能体，处理用户问题
        # 使用流式输出获取智能体的推理过程和最终结果
        # orchestrator.run返回一个生成器，逐步产出思考过程和结果
        # 他是有两个参数的 一个是llm 一个是lang llm是llm实例 可能会有think也可能是answer
        
        if label == "think":
            # 如果当前输出是思考过程
            _reasoning_content += _stream_text
            # 累积思考内容
            
            queue.put(["placeholder_think_stream_markdown", convert_think_message_to_markdown(_reasoning_content)])
            # 将思考过程转换为Markdown格式并发送到前端
            # 实现实时显示智能体的思考过程
            
            context["online_steps"][-1] = convert_think_message_to_markdown(_reasoning_content)
            # 更新上下文中最后一个步骤的内容
            # 保持在线步骤与当前显示内容同步
            
            api_queue.put(format_data(reasoning_content=_stream_text, id=request_id, stage="orchestrating"))
            # 将推理内容格式化后发送到API队列
            # 用于外部API调用或日志记录
            
        else:
            # 如果当前输出是最终结果
            result = _stream_text
            # 保存编排智能体的最终输出结果
            
    now_messages.append({"reasoning_content": _reasoning_content, "content": _stream_text, "role": "assistant", "stage": "orchestrating"})
    # 将编排阶段的完整信息添加到消息历史中
    # 包含推理过程、最终内容、角色和阶段信息
    
    context["if_search"] = result['if_search']
    # 从结果中提取是否需要搜索的标志
    # 用于决定是否执行网页搜索流程
    
    context["if_code"] = result['if_code']
    # 从结果中提取是否需要代码执行的标志
    # 用于决定是否执行代码生成和运行流程
    
    context["search_type"] = result['search_type']
    # 提取搜索类型信息
    # 指定使用哪种搜索引擎或搜索策略
    
    context["search_process"] = result['search_process']
    # 提取详细的搜索流程
    # 包含具体的搜索步骤和关键词

    raw_infos = []
    # 初始化原始信息列表
    # 用于存储所有搜索步骤的原始数据
    
    all_steps = step_by_step_process(context['search_process'])
    # 将搜索流程解析为分步执行的结构
    # 每个步骤包含描述、关键词等信息
    
    raw_info = [[] for _ in range(len(all_steps))]
    # 为每个步骤初始化空的原始信息列表
    # 预分配存储空间用于后续填充搜索结果
    
    raw_infos.append(raw_info)
    # 将初始化的原始信息结构添加到总列表中

    context['raw_info'] = raw_infos
    # 将原始信息保存到上下文中
    # 供后续步骤使用和更新
    
    context['search_res'] = raw_infos
    # 将搜索结果初始化为与原始信息相同的结构
    # 后续会根据搜索进展逐步填充
    
    context['llm_answer'] = None
    # 初始化LLM答案为None
    # 将在最后阶段由助手智能体生成


    if context['if_search'] == "否" and context['if_code'] == '否' or LANGUAGE == "en" and str(context['if_search']).lower() == "no" and str(context['if_code']).lower() == 'no':
        # 检查是否需要执行工具调用
        # 支持中文"否"和英文"no"两种表示方式
        # 如果既不需要搜索也不需要代码执行，则直接回答
        
        if debug_verbose:
            # 如果开启了详细调试模式
            queue.put(["bar", ":grey[🫢 智能体 · 当前问题无需 Function]"])
            # 向前端发送提示信息，表明无需使用工具
            
            context["online_steps"].append(":grey[🫢 智能体 · 当前问题无需 Function]")
            # 将此信息添加到在线步骤记录中
            
            start_time = time.time()
            # 记录开始时间，用于计算响应耗时
            
            llm_answer = ""
            # 初始化LLM答案字符串
            
            for label, _stream_text in llm.stream_chat(user_content=question):
                # 直接使用LLM进行流式对话
                # 不使用任何工具，仅基于模型知识回答
                
                if label == "answer":
                    # 如果当前输出是答案内容
                    llm_answer += _stream_text
                    # 累积答案文本
                    
                    api_queue.put(format_data(content=_stream_text, id=request_id, stage="answering without function calling"))
                    # 将答案内容发送到API队列
                    
                else:
                    # 如果是其他类型的输出
                    result = _stream_text
                    # 保存到结果变量中
                    
            context["online_answer"] = llm_answer
            # 将生成的答案保存到上下文中
            
            now_messages.append({"content": context["online_answer"], "role": "assistant", "stage": "answering without function calling"})
            # 将答案添加到消息历史中
            # 标记为无工具调用的直接回答阶段
            
            in_out = {"state": "model_answer", "input": question, "output": context["online_answer"], "cost_time": str(round(time.time()-start_time, 3))}
            # 构建输入输出记录
            # 包含状态、输入问题、输出答案和耗时信息
            
            model_logger.info(json.dumps(in_out, ensure_ascii=False))
            # 将记录以JSON格式写入日志
            # ensure_ascii=False确保中文字符正确显示
            
    else:
        # 如果需要使用工具（搜索或代码执行）
        all_evidences= [] # 将所有的证据（文本）信息都记录下来
        # 初始化证据列表，用于存储从网页搜索获得的所有文本证据
        
        code_evidences = [] # 将所有代码证据(文本)信息都记录下来
        # 初始化代码证据列表，用于存储代码执行相关的文本信息
        
        code_results_dict_list = [] # 把代码最原始的计算结果保存下来
        # 初始化代码结果字典列表，保存代码执行的原始输出
        
        empty_search = True
        # 初始化搜索空标志为True
        # 用于标记是否成功获取到搜索结果
        
        empty_code = True
        # 初始化代码空标志为True
        # 用于标记是否成功执行了代码
        
        use_tool_record = set()
        # 初始化已使用工具记录集合
        # 用于跟踪在整个流程中使用了哪些工具
        
        process_pipeline = ['system', 'user','step_by_step', 'assistant']
        # 定义处理流水线的阶段
        # system: 系统消息阶段
        # user: 用户消息阶段  
        # step_by_step: 分步执行阶段
        # assistant: 助手回答阶段
        
        for now_stage in process_pipeline:
            # 遍历处理流水线的每个阶段
            
            if now_stage == 'system':
                # 系统消息阶段
                now_messages.append(process_message(f"You are a helpful assistant. 当前的时间为{get_real_time_str()}。当前所在地: {get_location_by_ip()}。"))
                # 添加系统提示消息
                # 包含当前时间和地理位置信息，为模型提供上下文
                
            elif now_stage == 'user':
                # 用户消息阶段
                now_messages.append(process_message(content = context['question'], role = "user"))
                # 将用户问题格式化并添加到消息历史中
                
            elif now_stage == 'step_by_step':
                # 分步执行阶段
                # 进行路径的优化过程
                queue.put(["bar", "✏️ 智能体 · 路径优化"])
                # 通知前端开始路径优化阶段
                
                context["online_steps"].append("✏️ 智能体 · 路径优化")
                # 记录当前步骤到在线步骤列表
                
                queue.put(["placeholder_begin", None])
                # 发送占位符开始信号
                
                context["online_steps"].append("")
                # 为推理过程预留空位
                
                optimize_search_process_text = ""
                # 初始化优化后的搜索流程文本
                
                _reasoning_content = ""
                # 初始化推理内容
                
                for label, _stream_text in optimizer.run(context['search_process']):
                    # 运行优化智能体，优化搜索流程
                    
                    if label == "think":
                        # 如果是思考过程
                        _reasoning_content += _stream_text
                        # 累积推理内容
                        
                        queue.put(["placeholder_think_stream_markdown", convert_think_message_to_markdown(_reasoning_content)])
                        # 实时显示优化过程的思考
                        
                        context["online_steps"][-1] = convert_think_message_to_markdown(_reasoning_content)
                        # 更新在线步骤记录
                        
                        api_queue.put(format_data(reasoning_content=_stream_text, id=request_id, stage="optimize search process"))
                        # 发送到API队列
                        
                    else:
                        # 如果是最终结果
                        optimize_search_process_text = _stream_text
                        # 保存优化后的搜索流程
                        
                now_messages.append({"reasoning_content": _reasoning_content, "content": optimize_search_process_text, "role": "assistant", "stage": "optimize search process"})
                # 将优化阶段的信息添加到消息历史
                
                if len(optimize_search_process_text) != 0:
                    # 如果优化结果不为空
                    context['search_process'] = optimize_search_process_text
                    # 更新上下文中的搜索流程


                all_steps = step_by_step_process(context['search_process'])
                # 重新解析优化后的搜索流程
                # 生成新的分步执行结构
                
                latest_search_process = context['search_process'] # 记录上一步的search_process
                # 保存当前的搜索流程
                # 用于后续的动态调整和回滚
                
                for step_idx, step in enumerate(all_steps):
                    # 遍历所有搜索步骤
                    # step_idx: 当前步骤的索引
                    # step: 当前步骤的详细信息
                    
                    if "webSearch" in all_steps[step_idx]['step_desc']:    
                        # 如果当前步骤包含网页搜索                  
                        now_step_keywords = all_steps[step_idx]['now_step_keywords']
                        # 获取当前步骤的搜索关键词列表
                        
                        if len(now_step_keywords) == 0:
                            # 如果没有关键词
                            break
                            # 跳出循环，结束搜索流程

                        use_tool_record.add("webSearch")
                        # 记录使用了网页搜索工具
                        

                        empty_search, new_raw_info = fetch_search_result(all_steps, step_idx, context['raw_info'], debug_verbose, search_type=SEARCH_ENGINE, context=context, queue=queue)
                        # 执行搜索并获取结果
                        # empty_search: 是否搜索失败
                        # new_raw_info: 更新后的原始信息
                        
                        context['raw_info'] = new_raw_info  
                        # 更新上下文中的原始信息

                        if empty_search:
                            # 如果搜索失败
                            if debug_verbose:
                                # 在调试模式下显示错误信息
                                queue.put(["error", "当前访问人数过多，网页被挤爆啦，请稍后尝试..."])
                                # 向前端发送友好的错误提示
                            break
                            # 跳出循环，停止后续处理

                        # 更新 search_res (未下载正文)
                        new_search_res = update_search_res(all_steps, step_idx, context['search_res'], context['raw_info'], debug_verbose, context=context)
                        # 更新搜索结果数据结构
                        # 此时只包含搜索引擎返回的摘要信息，不包含完整网页内容
                        
                        context['search_res'] = new_search_res
                        # 将更新后的搜索结果保存到上下文

                        now_step_keywords = all_steps[step_idx]['now_step_keywords']
                        # 重新获取当前步骤的关键词（可能在处理过程中有所更新）
                        
                        now_step_keyword_idxs = all_steps[step_idx]['now_step_keyword_idxs']
                        # 获取关键词对应的索引列表
                        
                        argument_values_list = [[now_step_keyword] for now_step_keyword in now_step_keywords]
                        # 将关键词列表转换为函数调用参数格式
                        # 每个关键词都包装成一个单元素列表
                        
                        call_ids = [generate_call_id() for _ in range(len(now_step_keywords))]
                        # 为每个搜索关键词生成唯一的调用ID
                        # 用于追踪和匹配请求与响应
                        
                        # 整合关键词和对应的搜索结果
                        now_message = function_call_sent(argument_values_list, call_ids, "webSearch")
                        # 创建表示搜索工具调用的消息
                        # 符合OpenAI的function calling格式
                        
                        now_messages.append(now_message)
                        # 将工具调用消息添加到对话历史
                        
                        api_queue.put(format_data(reasoning_content="", id=request_id, stage="web search", tool_calls=now_message["tool_calls"]))
                        # 将工具调用信息发送到API队列
                        
                        now_search_res = []
                        # 初始化当前搜索结果列表
                        
                        now_raw_info = []
                        # 初始化当前原始信息列表
                        
                        for now_step_keyword_idx in now_step_keyword_idxs:
                            # 遍历当前步骤关键词的索引
                            now_search_res.append(context['search_res'][now_step_keyword_idx])
                            # 提取对应的搜索结果
                            
                            now_raw_info.append(context['raw_info'][now_step_keyword_idx])
                            # 提取对应的原始信息
                            
                        now_message = function_call_receive_snippet(now_step_keywords, call_ids, now_search_res, now_raw_info)
                        # 创建表示接收搜索结果的消息
                        # 包含搜索关键词和对应的网页摘要
                        
                        now_messages.extend(now_message)
                        # 将接收结果的消息添加到对话历史
                        # 使用extend因为可能返回多条消息
                        
                        api_queue.put(format_data(content=now_message, id=request_id, stage="web search"))
                        # 将搜索结果发送到API队列

                        idx_list = [] # 记录所有需要 URL 解析的文章 idx
                        # 初始化需要深度阅读的网页索引列表
                        
                        now_content = "" # CoT 过程
                        # 初始化当前内容字符串，用于记录推理过程
                        
                        now_evidence = [] # 记录当前拥有的所有证据信息
                        # 初始化当前证据列表
                        
                        snippet_list = []
                        # 初始化网页摘要列表

                        # 筛选相关的网页快照
                        for keyword_idx, now_search in enumerate(now_search_res):
                            # 遍历每个关键词的搜索结果
                            for doc_info in now_search:
                                # 遍历每个搜索结果文档
                                now_title = doc_info['title']
                                # 获取文档标题
                                
                                now_snippet = doc_info['snippet'].replace("\n", " ").replace("\r","")
                                # 获取文档摘要并清理换行符
                                # 将换行符替换为空格，保持文本连续性
                                
                                if len(now_snippet) == 0:
                                    # 如果摘要为空
                                    now_snippet = doc_info['title']
                                    # 使用标题作为摘要
                                
                                snippet_list.append(f"idx:{doc_info['idx']} snippet `{now_snippet}`")
                                # 将格式化的摘要添加到列表中
                                # 包含索引和摘要内容，便于后续处理

                        choose_snippet_list = []
                        # 初始化选中的摘要列表
                        
                        queue.put(["bar", "🔬 智能体 · 筛选相关网页"])
                        # 通知前端开始网页筛选阶段
                        
                        context["online_steps"].append("🔬 智能体 · 筛选相关网页")
                        # 记录当前步骤
                        
                        queue.put(["placeholder_begin", None])
                        # 开始占位符显示
                        
                        context["online_steps"].append("")
                        # 预留推理过程位置
                        
                        _reasoning_content = ""
                        # 初始化推理内容
                        
                        for label, _stream_text in selector.run(all_steps[step_idx]['step_desc'], snippet_list):
                            # 运行选择智能体，筛选相关网页
                            # 传入当前步骤描述和网页摘要列表
                            
                            if label == "think":
                                # 如果是思考过程
                                _reasoning_content += _stream_text
                                # 累积推理内容
                                
                                queue.put(["placeholder_think_stream_markdown", convert_think_message_to_markdown(_reasoning_content)])
                                # 实时显示筛选过程
                                
                                context["online_steps"][-1] = convert_think_message_to_markdown(_reasoning_content)
                                # 更新在线步骤
                                
                                api_queue.put(format_data(reasoning_content=_stream_text, id=request_id, stage="determine relevance"))
                                # 发送到API队列
                                
                            else:
                                # 如果是最终结果
                                choose_snippet_list = _stream_text
                                # 保存选中的网页索引列表
                                
                        api_queue.put(format_data(content=choose_snippet_list, id=request_id, stage="determine relevance"))
                        # 将选择结果发送到API队列
                        
                        now_messages.append({"reasoning_content": _reasoning_content, "content": choose_snippet_list, "role": "assistant", "stage": "determine relevance"})
                        # 将筛选阶段信息添加到消息历史
                        
                        new_snippet_list = []
                        # 初始化新的摘要列表
                        
                        if debug_verbose:
                            # 如果开启调试模式
                            render_text = ""
                            # 初始化渲染文本
                            
                            for choose_snippet_idx in choose_snippet_list:
                                # 遍历选中的网页索引
                                render_text += ":grey-background[" + "🔗" + str(choose_snippet_idx + 1) +"] "
                                # 生成带背景色的网页编号标签
                                # +1 是因为显示给用户的编号从1开始
                                
                            if len(render_text) == 0:
                                # 如果没有选中任何网页
                                render_text = ":grey-background[无]"
                                # 显示"无"
                                
                            queue.put(["bar", "🤔 智能体 · 和问题相关的网页有：" + render_text])
                            # 向前端显示选中的网页
                            
                            context["online_steps"].append("🤔 智能体 · 和问题相关的网页有：" + render_text)
                            # 记录到在线步骤
                            
                        for keyword_idx, now_search in enumerate(now_search_res):
                            # 遍历每个关键词的搜索结果
                            for doc_info in now_search:
                                # 遍历每个文档信息
                                if doc_info['idx'] in choose_snippet_list:
                                    # 如果文档索引在选中列表中
                                    now_snippet = doc_info['snippet'].replace("\n", " ").replace("\r","")
                                    # 清理摘要文本
                                    
                                    now_evidence.append({doc_info['idx']:f"{doc_info['title']}\nsnippet:{now_snippet}\nlink:{doc_info['url']}"})
                                    # 将文档信息作为证据添加到列表
                                    # 包含标题、摘要和链接
                                    
                                    new_snippet_list.append(f"idx:{doc_info['idx']} snippet `{now_snippet}`")
                                    # 添加到新摘要列表
                                    
                        snippet_list = new_snippet_list
                        # 更新摘要列表为筛选后的结果
                        
                        # 判断当前网页快照信息是否足够
                        if len(snippet_list) > 0: 
                            # 如果有选中的网页摘要
                            response = dict()
                            # 初始化响应字典
                            
                            queue.put(["bar", "🔬 智能体 · 判断网页数据是否足够"])
                            # 通知前端开始充分性验证
                            
                            context["online_steps"].append("🔬 智能体 · 判断网页数据是否足够")
                            # 记录当前步骤
                            
                            queue.put(["placeholder_begin", None])
                            # 开始占位符显示
                            
                            context["online_steps"].append("")
                            # 预留推理位置
                            
                            _reasoning_content = ""
                            # 初始化推理内容
                            
                            for label, _stream_text in validator.run(all_steps[step_idx]['step_desc'], "\n".join(snippet_list)):
                                # 运行充分性验证智能体
                                # 传入步骤描述和所有摘要信息
                                
                                if label == "think":
                                    # 如果是思考过程
                                    _reasoning_content += _stream_text
                                    # 累积推理内容
                                    
                                    queue.put(["placeholder_think_stream_markdown", convert_think_message_to_markdown(_reasoning_content)])
                                    # 实时显示验证过程
                                    
                                    context["online_steps"][-1] = convert_think_message_to_markdown(_reasoning_content)
                                    # 更新在线步骤
                                    
                                    api_queue.put(format_data(reasoning_content=_stream_text, id=request_id, stage="sufficency validating"))
                                    # 发送到API队列
                                    
                                else:
                                    # 如果是最终结果
                                    response = _stream_text
                                    # 保存验证结果
                                    
                            now_messages.append({"reasoning_content": _reasoning_content, "content": response, "role": "assistant", "stage": "sufficency validating"})
                            # 将验证阶段信息添加到消息历史
                            
                            now_content += response['analysis_sentence'] + "\n"
                            # 将分析句子添加到当前内容
                            
                            now_content += response['trans_sentence'] + "\n"
                            # 将转换句子添加到当前内容
                            
                            for snippet_sentence in response['snippet_sentence']:
                                # 遍历每个摘要句子的验证结果
                                now_content += snippet_sentence[2:] + "\n"
                                # 将句子（去掉前两个字符的标记）添加到内容
                                
                                match = re.search(r'idx:(\d+)', snippet_sentence)
                                # 使用正则表达式提取索引号
                                
                                if snippet_sentence[0] == '×':
                                    # 如果标记为不足够（×符号）
                                    if match:
                                        # 如果匹配到索引
                                        idx_number = int(match.group(1))
                                        # 提取索引数字
                                        # 说明当前网页快照需要解析URL内容
                                        idx_list.append(idx_number)
                                        # 将索引添加到需要深度解析的列表
                                        
                                else:
                                    # 如果标记为足够（✓符号）
                                    if match:
                                        # 如果匹配到索引
                                        idx_number = int(match.group(1))
                                        # 提取索引数字（此处仅提取，不需要深度解析）

                        # 解析URL内容
                        if len(idx_list) != 0:
                            # 如果有需要深度解析的网页
                            api_queue.put(format_data(content=idx_list, id=request_id, stage="sufficency validating"))
                            # 将需要解析的索引列表发送到API队列
                            
                            use_tool_record.add("mclick")
                            # 记录使用了网页阅读工具
                            
                            render_text = ""
                            # 初始化渲染文本
                            
                            for mclick_idx in idx_list:
                                # 遍历需要点击的网页索引
                                render_text += ":blue-background[" + "📃" + str(mclick_idx + 1) +"] "
                                # 生成蓝色背景的网页标签
                                # 📃 表示文档，+1 是因为用户界面从1开始计数
                                
                            queue.put(["bar", ":grey[😮 智能体 · 当前网页的信息似乎不太够，打开网页看一看...]"])
                            # 向前端发送提示信息
                            
                            context["online_steps"].append(":grey[😮 智能体 · 当前网页的信息似乎不太够，打开网页看一看...]")
                            # 记录到在线步骤
                            
                            queue.put(["bar", "🤨 智能体 · 这些网页需要打开：" + render_text])
                            # 显示具体需要打开的网页
                            
                            context["online_steps"].append("🤨 智能体 · 这些网页需要打开：" + render_text)
                            # 记录具体的网页信息

                            queue.put(["bar", "📖 调工具 · 网页阅读"])
                            # 通知前端开始网页阅读工具调用
                            
                            context["online_steps"].append("📖 调工具 · 网页阅读")
                            # 记录工具调用步骤
                            
                            argument_values_list = [idx_list]
                            # 将索引列表作为参数
                            
                            call_ids = [generate_call_id()] 
                            # 生成调用ID
                            
                            # 整合URL和对应的解析内容
                            now_message = function_call_sent([argument_values_list], call_ids, "mclick", ["idx_list"], now_content)
                            # 创建网页阅读工具调用消息
                            # 包含要阅读的网页索引列表和当前分析内容
                            
                            now_messages.append(now_message)
                            # 添加到消息历史
                            
                            api_queue.put(format_data(reasoning_content="", id=request_id, stage="fetch page body", tool_calls=now_message["tool_calls"]))
                            # 发送工具调用到API队列
                            
                            now_message = function_call_receive_document(idx_list, call_ids, now_search_res, context=context, queue=queue)
                            # 处理网页文档获取的结果
                            # 实际抓取和解析网页内容
                            
                            api_queue.put(format_data(content=now_message, id=request_id, stage="fetch page body"))
                            # 发送网页内容到API队列
                            
                            now_messages.append(now_message)
                            # 添加到消息历史
                            
                            document_list = json.loads(now_message['content'])
                            # 解析获取到的文档列表

                            # 更新evidence，将 document_list 中出现的，用正文信息代替原来证据句对应的网页快照
                            for i, evi_dict in enumerate(now_evidence):
                                # 遍历当前证据列表
                                key1 = next(iter(evi_dict))
                                # 获取证据字典的键（网页索引）
                                
                                for doc_dict in document_list:
                                    # 遍历文档列表
                                    key2 = next(iter(doc_dict))
                                    # 获取文档字典的键
                                    
                                    if str(key1) == str(key2):
                                        # 如果索引匹配
                                        now_evidence[i][key1] = doc_dict[key2]
                                        # 用完整文档内容替换原来的摘要信息
                                        
                        else:
                            # 如果网页摘要信息已经足够
                            queue.put(["bar","😏 智能体 · 分析完毕"])
                            # 通知前端分析完成
                            
                            context["online_steps"].append("😏 智能体 · 分析完毕")
                            # 记录完成步骤
                            
                            queue.put(["divider", None])
                            # 添加分隔线
                            
                            context["online_steps"].append("\n---\n")
                            # 记录分隔线到步骤历史
                            
                        now_evidence_list = [json.dumps(evi_dict,ensure_ascii=False) for evi_dict in now_evidence]
                        # 将证据字典列表转换为JSON字符串列表
                        # ensure_ascii=False确保中文字符正确编码
                        
                        all_evidences.extend(now_evidence_list)
                        # 将当前步骤的证据添加到总证据列表
                        
                        if len(now_evidence_list) > 0:
                            # 如果当前步骤获得了证据
                            # 根据当前的状态信息（当前evidence、当前步骤、整体步骤）重新规划路径
                            if step_idx != len(all_steps) - 1:
                                # 如果不是最后一个步骤
                                response = dict()
                                # 初始化响应字典
                                
                                queue.put(["bar","🔬 智能体 · 依据当前状态重新规划路径"])
                                # 通知前端开始路径重新规划
                                
                                context["online_steps"].append("🔬 智能体 · 依据当前状态重新规划路径")
                                # 记录当前步骤
                                
                                queue.put(["placeholder_begin", None])
                                # 开始占位符显示
                                
                                context["online_steps"].append("")
                                # 预留推理位置
                                
                                _reasoning_content = ""
                                # 初始化推理内容
                                
                                for label, _stream_text in reorchestrator.run(context['question'], now_evidence_list, all_steps[step_idx]['step_desc'], latest_search_process):
                                    # 运行重新编排智能体
                                    # 传入问题、当前证据、当前步骤描述和最新搜索流程
                                    
                                    if label == "think":
                                        # 如果是思考过程
                                        _reasoning_content += _stream_text
                                        # 累积推理内容
                                        
                                        queue.put(["placeholder_think_stream_markdown", convert_think_message_to_markdown(_reasoning_content)])
                                        # 实时显示重新规划过程
                                        
                                        context["online_steps"][-1] = convert_think_message_to_markdown(_reasoning_content)
                                        # 更新在线步骤
                                        
                                        api_queue.put(format_data(reasoning_content=_stream_text, id=request_id, stage="reorchestrate"))
                                        # 发送到API队列
                                        
                                    else:
                                        # 如果是最终结果
                                        response = _stream_text
                                        # 保存重新规划的结果
                                        
                                now_messages.append({"reasoning_content": _reasoning_content, "content": response, "role": "assistant", "stage": "reorchestrate"})
                                # 将重新规划阶段信息添加到消息历史
                                
                                latest_search_process = response['update_whole_step']
                                # 更新最新的搜索流程
                                
                                all_steps = step_by_step_process(latest_search_process)
                                # 重新解析更新后的搜索流程
                                
                                queue.put(["bar",f"🔨更新为流程：{latest_search_process}"])
                                # 显示更新后的流程
                                
                                context["online_steps"].append(f"🔨更新为流程：{latest_search_process}")
                                # 记录流程更新
                                
                                api_queue.put(format_data(content=latest_search_process, id=request_id, stage="reorchestrate"))
                                # 发送更新流程到API队列
                                
                            else:
                                # 如果是最后一个步骤
                                context['search_process'] = latest_search_process
                                # 保存最终搜索流程
                                
                                break
                                # 跳出步骤循环
                                
                        else:
                            # 如果当前步骤没有获得证据
                            start_index = latest_search_process.find("-> " + all_steps[step_idx]['step_desc']) 
                            # 找到当前步骤在搜索流程中的位置
                            
                            latest_search_process = latest_search_process[:start_index] + "-> " + all_steps[step_idx]['step_desc']
                            # 截断搜索流程到当前步骤
                            
                            all_steps = step_by_step_process(latest_search_process)
                            # 重新解析截断后的搜索流程
                            
                            context['search_process'] = latest_search_process
                            # 更新上下文中的搜索流程
                            
                            break
                            # 跳出步骤循环

                    else:
                        # 如果当前步骤不包含网页搜索（即包含代码执行）
                        empty_code = False
                        # 标记代码执行不为空
                        
                        use_tool_record.add("codeRunner")
                        # 记录使用了代码执行工具
                        
                        now_step_keywords = all_steps[step_idx]['now_step_keywords']
                        # 获取当前步骤的关键词（用于代码生成）
                        
                        if len(now_step_keywords) == 0:
                            # 如果没有关键词
                            if debug_verbose:
                                # 调试模式下可以添加相关日志
                                pass
                            continue
                            # 跳过当前步骤
                            
                        # 构建参考信息
                        if step_idx == 0:
                            # 如果是第一个步骤
                            if LANGUAGE == "en":
                                previous_reference = "None"
                                # 英文环境下设置为"None"
                            else:
                                previous_reference = "无"
                                # 中文环境下设置为"无"
                        else:
                            # 如果不是第一个步骤
                            previous_reference = all_steps[step_idx - 1]['step_desc'] # 把上一步作为参考信息
                            # 使用上一步的描述作为参考
                            
                        all_codes, all_code_results = run_code(code_agent, code_executor, meta_data,all_steps, step_idx, context['question'], previous_reference, all_evidences, debug_verbose, context=context, queue=queue, api_queue=api_queue, request_id=request_id)
                        # 执行代码生成和运行的完整流程
                        # 返回生成的代码列表和执行结果列表
                        
                        code_results_dict_list.extend(all_code_results)
                        # 将代码执行结果添加到总结果列表
                        
                        argument_values_list = [[all_code] for all_code in all_codes]
                        # 将代码列表转换为参数格式
                        
                        call_ids = [generate_call_id() for _ in range(len(now_step_keywords))]
                        # 为每个代码生成调用ID

                        # 整合生成代码和代码的执行结果
                        now_message = function_call_sent(argument_values_list, call_ids, "codeRunner", argument_names = ['code'])
                        # 创建代码执行工具调用消息
                        # 包含生成的代码和调用ID
                        
                        now_messages.append(now_message)
                        # 添加到消息历史
                        
                        code_evidence, now_message = function_call_receive_code_results(all_steps[step_idx]['now_step_keywords'], all_codes, call_ids, all_code_results)
                        # 处理代码执行结果
                        # 返回代码证据和响应消息
                        
                        now_messages.extend(now_message)
                        # 将结果消息添加到历史
                        
                        code_evidences.extend(code_evidence)
                        # 将代码证据添加到总证据列表
                        
                        # 根据当前的状态信息（当前代码执行结果、当前步骤、整体步骤）重新规划路径
                        if step_idx != len(all_steps) - 1:
                            # 如果不是最后一个步骤
                            all_code_results_list = []
                            # 初始化代码结果字符串列表
                            
                            for all_code_result in all_code_results:
                                # 遍历所有代码执行结果
                                all_code_results_list.append(str(all_code_result))
                                # 转换为字符串格式
                                
                            response = dict()
                            # 初始化响应字典
                            
                            queue.put(["bar", "🔬 智能体 · 依据当前状态重新规划路径"])
                            # 通知前端开始重新规划
                            
                            context["online_steps"].append("🔬 智能体 · 依据当前状态重新规划路径")
                            # 记录当前步骤
                            
                            queue.put(["placeholder_begin", None])
                            # 开始占位符显示
                            
                            context["online_steps"].append("")
                            # 预留推理位置
                            
                            _reasoning_content = ""
                            # 初始化推理内容
                            
                            for label, _stream_text in reorchestrator.run(context['question'], all_code_results_list, all_steps[step_idx]['step_desc'], latest_search_process):
                                # 运行重新编排智能体
                                # 传入问题、代码结果、当前步骤和最新流程
                                
                                if label == "think":
                                    # 如果是思考过程
                                    _reasoning_content += _stream_text
                                    # 累积推理内容
                                    
                                    queue.put(["placeholder_think_stream_markdown", convert_think_message_to_markdown(_reasoning_content)])
                                    # 实时显示重新规划过程
                                    
                                    context["online_steps"][-1] = convert_think_message_to_markdown(_reasoning_content)
                                    # 更新在线步骤
                                    
                                    api_queue.put(format_data(reasoning_content=_stream_text, id=request_id, stage="reorchestrate"))
                                    # 发送到API队列
                                    
                                elif label == "answer":
                                    # 如果是答案内容
                                    response = _stream_text
                                    # 保存重新规划结果
                                    
                            now_messages.append({"reasoning_content": _reasoning_content, "content": "response", "role": "assistant", "stage": "reorchestrate"})
                            # 将重新规划信息添加到消息历史
                            
                            latest_search_process = response['update_whole_step']
                            # 更新最新搜索流程
                            
                            all_steps = step_by_step_process(latest_search_process)
                            # 重新解析更新后的流程
                            
                            queue.put(["bar", f"🔨更新为流程：{latest_search_process}"])
                            # 显示更新后的流程
                            
                            context["online_steps"].append(f"🔨更新为流程：{latest_search_process}")
                            # 记录流程更新
                            
                            api_queue.put(format_data(content=latest_search_process, id=request_id, stage="reorchestrate"))
                            # 发送更新流程到API队列
                            
                        else:
                            # 如果是最后一个步骤
                            context['search_process'] = latest_search_process
                            # 保存最终搜索流程
                            
                            break
                            # 跳出步骤循环
                        

            elif now_stage == 'assistant':
                # 助手阶段 - 生成最终答案
                if len(all_evidences) == 0 or empty_search == True:
                    # 如果没有获得任何证据或搜索失败
                    if LANGUAGE == "en":
                        all_evidences.append("There is no evidence, please reject to answer.")
                        # 英文环境添加拒绝回答的提示
                    else:
                        all_evidences.append("当前无证据句子，请拒绝回答。")
                        # 中文环境添加拒绝回答的提示
                        
                _reasoning_content = ""
                # 初始化推理内容
                
                llm_answer = ""
                # 初始化LLM答案
                
                queue.put(["bar", "🖥️ 智能体 · 综合获取的信息"])
                # 通知前端开始信息综合阶段
                
                context["online_steps"].append("🖥️ 智能体 · 综合获取的信息")
                # 记录当前步骤
                
                queue.put(["placeholder_begin", None])
                # 开始占位符显示
                
                context["online_steps"].append("")
                # 预留推理位置
                
                for label, _stream_text in assitant.run(context['question'], context['search_process'], all_evidences, code_evidences):
                    # 运行助手智能体
                    # 传入问题、搜索流程、所有文本证据和代码证据
                    
                    if label == "think":
                        # 如果是思考过程
                        _reasoning_content += _stream_text
                        # 累积推理内容
                        
                        queue.put(["placeholder_think_stream_markdown", convert_think_message_to_markdown(_reasoning_content)])
                        # 实时显示答案生成过程
                        
                        context["online_steps"][-1] = convert_think_message_to_markdown(_reasoning_content)
                        # 更新在线步骤
                        
                        api_queue.put(format_data(reasoning_content=_stream_text, id=request_id, stage="answer with function call"))
                        # 发送到API队列
                        
                    elif label == "answer":
                        # 如果是答案内容
                        llm_answer += _stream_text
                        # 累积答案文本
                        
                        api_queue.put(format_data(content=_stream_text, id=request_id, stage="answer with function call"))
                        # 发送答案片段到API队列
                        
                    else:
                        # 如果是其他类型输出
                        llm_answer = _stream_text
                        # 直接赋值为答案
                        
                now_messages.append({"reasoning_content": _reasoning_content, "content": llm_answer, "role": "assistant", "stage": "answer with function call"})
                # 将答案生成阶段信息添加到消息历史
                
                llm_no_ref_answer = remove_ref_tag(llm_answer)
                # 移除答案中的引用标记，生成无引用版本
                
                context['llm_answer'] = llm_answer
                # 保存原始答案（包含引用标记）到上下文
                
                if debug_verbose:
                    # 如果开启调试模式
                    ref2md_answer = replace_ref_tag2md(llm_answer, context["online_url_lists"])
                    # 将引用标记转换为Markdown链接格式
                    
                    ref2md_answer = latex_render(ref2md_answer)
                    # 处理LaTeX格式内容
                    
                    context["online_code_results"] = code_results_dict_list
                    # 保存代码执行结果到上下文
                    
                    context["online_answer"] = ref2md_answer
                    # 保存处理后的答案到上下文
                    
                now_messages.append(process_message(content = llm_no_ref_answer, role = "assistant", content_ref = llm_answer))
                # 添加最终答案消息到历史
                # 包含无引用版本和带引用的原始版本

        meta_data = {
            "time_stamp":f"{get_real_time_str()}",
            "question": context['question'],
            "feedback": None,
            "messages" : now_messages,
            "tool_choice": "auto",
            "parallel_tool_calls": True,
            "tools": get_tool_list(use_tool_record)
        }
        # 构建完整的元数据记录
        # time_stamp: 时间戳
        # question: 原始问题
        # feedback: 用户反馈（暂为空）
        # messages: 完整对话历史
        # tool_choice: 工具选择策略
        # parallel_tool_calls: 是否支持并行工具调用
        # tools: 实际使用的工具列表
        
        # 将有效信息收集起来
        if empty_search == False or empty_code == False:
            # 如果成功执行了搜索或代码（有有效信息）
            context["new_record"] = meta_data
            # 将元数据保存到上下文
            
            if meta_verbose:
                # 如果开启元数据详细输出
                print("### json 最后存储格式如下：")
                # 打印提示信息
                
                print(json.dumps(meta_data, indent=4, ensure_ascii=False))
                # 以格式化JSON形式打印元数据

            if len(save_jsonl_path) > 0:
                # 如果指定了保存路径
                with open(save_jsonl_path, 'a', encoding='utf-8') as f:
                    # 以追加模式打开文件
                    json_line = json.dumps(meta_data, ensure_ascii=False)
                    # 将元数据序列化为JSON字符串
                    
                    f.write(json_line + '\n')
                    # 写入文件，每条记录占一行（JSONL格式）
                    
    queue.put(["finish", None])
    # 向消息队列发送完成信号
    
    api_queue.put("finish")
    # 向API队列发送完成信号
    
    return
    # 函数执行完毕返回 