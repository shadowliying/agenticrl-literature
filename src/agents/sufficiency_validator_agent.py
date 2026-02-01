# encoding: utf-8
# 文件编码声明，指定使用 UTF-8 编码格式

import time
# 导入时间模块，用于计算代码执行时间

import json
# 导入 JSON 模块，用于记录日志时将数据序列化为 JSON 格式

import re
# 导入正则表达式模块，用于文本处理和模式匹配

from llms.base_llm import BaseLLM
# 从 llms.base_llm 模块导入 BaseLLM 基础大语言模型类

from utils.logger import model_logger
# 从 utils.logger 模块导入 model_logger，用于记录模型运行日志

from .base_agent import BaseAgent
# 从当前包的 base_agent 模块导入 BaseAgent 基础智能体类

from .prompts.sufficiency_validator_agent_prompts import SYSTEM_PROMPT2, SYSTEM_PROMPT2_EN
# 从 prompts.sufficiency_validator_agent_prompts 模块导入中文和英文的系统提示词
# SYSTEM_PROMPT2: 中文系统提示词，用于指导模型验证信息充分性
# SYSTEM_PROMPT2_EN: 英文系统提示词，用于指导模型验证信息充分性

class SufficiencyValidatorAgent(BaseAgent):
    # 定义 SufficiencyValidatorAgent 类，继承自 BaseAgent 基础智能体类
    # 这是一个专门用于验证给定信息是否足够回答用户问题的智能体
    # 主要功能是分析快照内容，判断每个快照是否提供足够的信息来回答问题
    
    def __init__(self, llm: BaseLLM, lang: str):
        # 构造函数，初始化 SufficiencyValidatorAgent 实例
        # 参数详解：
        # - llm: BaseLLM 类型，大语言模型实例，用于理解和分析文本内容
        #   该模型将负责分析用户问题和快照内容，判断信息是否充分
        # - lang: str 类型，语言设置，用于选择对应的提示词模板和后处理方法
        #   * "zh" 表示中文模式，使用中文提示词和中文后处理
        #   * "en" 表示英文模式，使用英文提示词和英文后处理
        
        self.llm = llm
        # 将传入的大语言模型实例赋值给实例变量 self.llm
        # 这个模型将负责分析问题需求、评估快照信息充分性
        
        self.lang = lang
        # 将传入的语言设置赋值给实例变量 self.lang
        # 用于后续选择合适的中文或英文提示词模板和后处理方法

    def postprocess(self, response_text):
        # 定义 postprocess 方法，用于后处理模型返回的响应文本
        # 参数详解：
        # - response_text: str 类型，模型返回的原始响应文本
        #   包含问题分析、过渡短语和快照分析等结构化内容
        
        res = dict()
        # 初始化结果字典，用于存储解析后的结构化数据
        
        if self.lang == "zh":
            # 如果语言设置为中文
            res = self.postprocess_zh(response_text)
            # 调用中文后处理方法
        elif self.lang == "en":
            # 如果语言设置为英文
            res = self.postprocess_en(response_text)
            # 调用英文后处理方法
        
        return res
        # 返回解析后的结构化结果字典
    
    def postprocess_zh(self, response):
        # 定义 postprocess_zh 方法，用于处理中文响应文本
        # 参数详解：
        # - response: str 类型，模型返回的中文响应文本
        #   格式包含【问题分析】、【过渡短语】、【快照分析】等部分
        
        analysis_sentence = response.split("【过渡短语】")[0].split("【问题分析】")[-1].strip()
        # 提取问题分析部分
        # 处理逻辑：
        # 1. 先用 "【过渡短语】" 分割，取第一部分
        # 2. 再用 "【问题分析】" 分割，取最后一部分
        # 3. 去除前后空白字符
        # 例如：从 "【问题分析】需要分析建筑用途【过渡短语】" 中提取 "需要分析建筑用途"
        
        trans_sentence = response.split("【快照分析】")[0].split("【过渡短语】")[-1].strip()
        # 提取过渡短语部分
        # 处理逻辑：
        # 1. 先用 "【快照分析】" 分割，取第一部分
        # 2. 再用 "【过渡短语】" 分割，取最后一部分
        # 3. 去除前后空白字符
        # 例如：从 "【过渡短语】根据搜索结果【快照分析】" 中提取 "根据搜索结果"
        
        snippet_sentence = response.split("【快照分析】")[-1].strip()
        # 提取快照分析部分
        # 处理逻辑：
        # 1. 用 "【快照分析】" 分割，取最后一部分
        # 2. 去除前后空白字符
        # 例如：从 "【快照分析】√ 快照0信息充分 × 快照1信息不足" 中提取 "√ 快照0信息充分 × 快照1信息不足"
        
        if len(snippet_sentence.split("【")) > 1: # 处理重复
            # 如果快照分析部分还包含其他【】标记（说明有重复内容）
            snippet_sentence = snippet_sentence.split("【")[0]
            # 只取第一个【】标记之前的内容，避免重复解析

        res = {
            "analysis_sentence": analysis_sentence,
            # 问题分析句子，描述回答用户问题需要什么信息
            "trans_sentence": trans_sentence,
            # 过渡短语，连接问题分析和快照分析的过渡语句
            "snippet_sentence": [sentence for sentence in snippet_sentence.split("\n") if len(sentence)>0 and sentence[0] in ['×', '√']]
            # 快照分析句子列表，只保留以 × 或 √ 开头的行
            # 过滤逻辑：
            # 1. 按换行符分割
            # 2. 只保留非空行
            # 3. 只保留以 ×（信息不足）或 √（信息充分）开头的行
        }
        return res
        # 返回解析后的结构化结果

    def postprocess_en(self, response):
        # 定义 postprocess_en 方法，用于处理英文响应文本
        # 参数详解：
        # - response: str 类型，模型返回的英文响应文本
        #   格式包含【Question Analysis】、【Transition Phrase】、【Snippet Analysis】等部分
        
        analysis_sentence = response.split("【Transition Phrase】")[0].split("【Question Analysis】")[-1].strip()
        # 提取问题分析部分（英文版本）
        # 处理逻辑与中文版本相同，但使用英文标记
        
        trans_sentence = response.split("【Snippet Analysis】")[0].split("【Transition Phrase】")[-1].strip()
        # 提取过渡短语部分（英文版本）
        # 处理逻辑与中文版本相同，但使用英文标记
        
        snippet_sentence = response.split("【Snippet Analysis】")[-1].strip()
        # 提取快照分析部分（英文版本）
        # 处理逻辑与中文版本相同，但使用英文标记
        
        if len(snippet_sentence.split("【")) > 1: # 处理重复
            # 如果快照分析部分还包含其他【】标记（说明有重复内容）
            snippet_sentence = snippet_sentence.split("【")[0]
            # 只取第一个【】标记之前的内容，避免重复解析

        res = {
            "analysis_sentence": analysis_sentence,
            # 问题分析句子（英文），描述回答用户问题需要什么信息
            "trans_sentence": trans_sentence,
            # 过渡短语（英文），连接问题分析和快照分析的过渡语句
            "snippet_sentence": [sentence for sentence in snippet_sentence.split("\n") if len(sentence)>0 and sentence[0] in ['×', '√']]
            # 快照分析句子列表（英文），只保留以 × 或 √ 开头的行
            # 过滤逻辑与中文版本相同
        }
        return res
        # 返回解析后的结构化结果

    def run(self, query, snippet_list, temperature=0.3, max_tokens=2048):
        # 定义 run 方法，这是 SufficiencyValidatorAgent 的主要执行方法
        # 参数详解：
        # - query: str 类型，用户提出的问题或查询内容
        #   例如："什么是机器学习？" 或 "请介绍深度学习的基本概念"
        # - snippet_list: list 类型，包含多个文本快照的列表
        #   每个快照是一个字符串，可能来自搜索结果、文档片段等
        #   例如：["快照1内容", "快照2内容", "快照3内容", ...]
        # - temperature: float 类型，温度参数，控制生成文本的随机性
        #   * 默认值 0.3，表示相对保守和确定性的输出
        #   * 值越低，输出越确定和一致，适合验证任务
        #   * 值越高，输出越随机和多样化
        # - max_tokens: int 类型，最大生成 token 数量
        #   * 默认值 2048，限制模型输出的最大长度
        #   * 对于验证任务，通常需要较长的分析输出
        
        start_time = time.time()
        # 记录开始时间，用于计算整个方法的执行时长
        # 精确到毫秒级别，用于性能监控和日志记录
        
        user_prompt = ""
        # 初始化用户提示词变量，用于存储构建的用户提示词
        
        systemt_prompt = ""
        # 初始化系统提示词变量，用于存储选择的中文或英文系统提示词
        # 注意：变量名中有拼写错误，应该是 system_prompt
        
        if self.lang == "zh":
            # 如果语言设置为中文
            user_prompt = f"""【问题】\n以下信息能够满足当前这步 {query} 检索所需的所有信息吗?\n【快照】{snippet_list}\n"""
            # 构建中文用户提示词模板
            # 模板结构：
            # - 【问题】：用户的具体问题
            # - 【快照】：所有需要验证的快照内容
            # 问题焦点：判断快照信息是否足够回答用户问题
            systemt_prompt = SYSTEM_PROMPT2
            # 使用中文系统提示词，指导模型如何验证信息充分性
        elif self.lang == "en":
            # 如果语言设置为英文
            user_prompt = f"""【Question】\nCan the following information fulfill all the requirements needed for the current retrieval of {query} ?\n【Snippet】{snippet_list}\n"""
            # 构建英文用户提示词模板
            # 模板结构与中文类似，但使用英文表述
            systemt_prompt = SYSTEM_PROMPT2_EN
            # 使用英文系统提示词，指导模型如何验证信息充分性

        response = ""
        # 初始化响应字符串，用于累积模型的输出内容
        # 这个响应将包含问题分析、过渡短语和快照分析等结构化内容
        
        reasoning_content = ""
        # 初始化推理内容字符串，用于累积模型的思考过程
        # 如果模型支持思考过程输出，这里会记录模型的推理逻辑
        
        for label, cont in self.llm.stream_chat(system_content=systemt_prompt, user_content=user_prompt, temperature=temperature, max_tokens=max_tokens, answer_sleep=0):
            # 调用大语言模型的流式聊天方法
            # 参数详解：
            # - system_content: 系统提示词，指导模型的行为和任务要求
            # - user_content: 用户提示词，包含具体的问题和快照内容
            # - temperature: 温度参数，控制输出的随机性
            # - max_tokens: 最大输出token数
            # - answer_sleep: 设置为0，表示不延迟输出
            # 返回：标签和内容的迭代器，标签可能是"think"或"response"
            
            if label == "think":
                # 如果标签是 "think"，表示这是模型的思考过程
                reasoning_content = cont
                # 将思考内容赋值给推理内容变量
                yield label, reasoning_content
                # 生成器yield，向调用者返回思考过程和内容
            else:
                # 如果标签不是 "think"，表示这是模型的正式响应
                response += cont
                # 将内容添加到响应字符串中，累积完整的响应内容
        
        res = self.postprocess(response)
        # 调用后处理方法，将原始响应文本解析为结构化数据
        # 返回包含 analysis_sentence、trans_sentence、snippet_sentence 的字典
        
        in_out = {"state": "parse_classify", "input": {"question": query, "snippet_list": snippet_list, "temperature": temperature, "max_tokens": max_tokens}, \
                "output": res, "response": {"content":response, "reasoning_content": reasoning_content}, "user_prompt": user_prompt, "cost_time": str(round(time.time()-start_time, 3))}
        # 构建日志记录字典，包含完整的输入输出信息
        # 字典结构详解：
        # - state: 当前状态 "parse_classify"，表示正在执行信息充分性验证任务
        # - input: 输入参数
        #   * question: 用户问题
        #   * snippet_list: 所有快照的列表
        #   * temperature: 温度参数
        #   * max_tokens: 最大token数
        # - output: 输出的解析结果（包含问题分析、过渡短语、快照分析）
        # - response: 模型响应
        #   * content: 模型的完整响应内容
        #   * reasoning_content: 模型的思考过程
        # - user_prompt: 构建的用户提示词
        # - cost_time: 执行时间（四舍五入到3位小数，单位：秒）
        
        model_logger.info(json.dumps(in_out, ensure_ascii=False))
        # 将日志字典转换为JSON格式并记录到日志中
        # ensure_ascii=False 确保中文字符正常显示，不会被转义为Unicode编码
        
        yield "answer", res
        # 生成器yield，向调用者返回最终结果
        # 标签为 "answer"，内容为解析后的结构化验证结果
        # 包含问题分析、过渡短语和每个快照的充分性评估