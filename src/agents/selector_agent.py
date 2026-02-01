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

from .prompts.selector_agent_prompts import SYSTEM_PROMPT5, SYSTEM_PROMPT5_EN
# 从 prompts.selector_agent_prompts 模块导入中文和英文的系统提示词
# SYSTEM_PROMPT5: 中文系统提示词，用于指导模型选择相关快照
# SYSTEM_PROMPT5_EN: 英文系统提示词，用于指导模型选择相关快照

class SelectorAgent(BaseAgent):
    # 定义 SelectorAgent 类，继承自 BaseAgent 基础智能体类
    # 这是一个专门用于从多个文本快照中选择与用户问题最相关的快照的智能体
    
    def __init__(self, llm: BaseLLM, lang: str):
        # 构造函数，初始化 SelectorAgent 实例
        # 参数详解：
        # - llm: BaseLLM 类型，大语言模型实例，用于理解和分析文本内容
        # - lang: str 类型，语言设置，用于选择对应的提示词模板
        #   * "zh" 表示中文模式，使用中文提示词
        #   * "en" 表示英文模式，使用英文提示词
        
        self.llm = llm
        # 将传入的大语言模型实例赋值给实例变量 self.llm
        # 这个模型将负责理解用户问题和快照内容，并做出相关性判断
        
        self.lang = lang
        # 将传入的语言设置赋值给实例变量 self.lang
        # 用于后续选择合适的中文或英文提示词模板

    def run(self, query, snippet_list, temperature=0.3, max_tokens=2048):
        # 定义 run 方法，这是 SelectorAgent 的主要执行方法
        # 参数详解：
        # - query: str 类型，用户提出的问题或查询内容
        #   例如："什么是人工智能？" 或 "请介绍机器学习的基本概念"
        # - snippet_list: list 类型，包含多个文本快照的列表
        #   每个快照是一个字符串，可能来自搜索结果、文档片段等
        #   例如：["快照1内容", "快照2内容", "快照3内容", ...]
        # - temperature: float 类型，温度参数，控制生成文本的随机性
        #   * 默认值 0.3，表示相对保守和确定性的输出
        #   * 值越低，输出越确定和一致
        #   * 值越高，输出越随机和多样化
        # - max_tokens: int 类型，最大生成 token 数量
        #   * 默认值 2048，限制模型输出的最大长度
        #   * 对于选择任务，通常不需要很长的输出
        
        start_time = time.time()
        # 记录开始时间，用于计算整个方法的执行时长
        # 精确到毫秒级别，用于性能监控和日志记录
        
        snippet_str = "\n".join(snippet_list)
        # 将快照列表中的所有快照用换行符连接成一个字符串
        # 这样做是为了方便在提示词中展示所有快照内容
        # 例如：["快照1", "快照2", "快照3"] -> "快照1\n快照2\n快照3"
        
        system_prompt = ""
        # 初始化系统提示词变量，用于存储选择的中文或英文系统提示词
        
        user_prompt = ""
        # 初始化用户提示词变量，用于存储构建的用户提示词
        
        if self.lang == "zh":
            # 如果语言设置为中文
            user_prompt = f"【问题】\n以下信息和当前检索 {query} 相关的是哪几个快照？\n【快照】\n{snippet_str}\n【索引列表】\n"
            # 构建中文用户提示词模板
            # 模板结构：
            # - 【问题】：用户的具体问题
            # - 【快照】：所有可选的快照内容
            # - 【索引列表】：要求模型返回相关快照的索引
            system_prompt = SYSTEM_PROMPT5
            # 使用中文系统提示词，指导模型如何理解和执行选择任务
        elif self.lang == "en":
            # 如果语言设置为英文
            user_prompt = f"【Question】\nWhich snippets are relevant to the current search {query} ?\n【Snippet】\n{snippet_str}\n【Index list】\n"
            # 构建英文用户提示词模板
            # 模板结构与中文类似，但使用英文表述
            system_prompt = SYSTEM_PROMPT5_EN
            # 使用英文系统提示词，指导模型如何理解和执行选择任务

        response = ""
        # 初始化响应字符串，用于累积模型的输出内容
        # 这个响应将包含模型选择的相关快照索引
        
        reasoning_content = ""
        # 初始化推理内容字符串，用于累积模型的思考过程
        # 如果模型支持思考过程输出，这里会记录模型的推理逻辑
        
        for label, cont in self.llm.stream_chat(system_content=system_prompt, user_content=user_prompt, temperature=temperature, max_tokens=max_tokens, answer_sleep=0):
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
        
        try:
            # 尝试解析模型返回的响应，提取索引列表
            response = re.sub(r"[^\[\]\d,]", "", response)
            # 使用正则表达式清理响应文本
            # 正则表达式 r"[^\[\]\d,]" 的含义：
            # - [^...] 表示匹配不在括号内的字符
            # - \[\]: 匹配方括号字符
            # - \d: 匹配数字字符
            # - ,: 匹配逗号字符
            # 所以这个正则表达式会保留方括号、数字和逗号，删除其他所有字符
            # 例如："我认为相关的快照是[0, 2, 4]" -> "[0,2,4]"
            
            related_snippet_idx_list = eval(response)
            # 使用 eval() 函数将清理后的字符串转换为Python列表
            # 例如："[0,2,4]" -> [0, 2, 4]
            # 注意：使用eval()需要确保输入是安全的，这里已经通过正则表达式清理了
            # 类型从 str 变成 list[int]
        except Exception as e:
            # 如果解析失败（例如eval()出错或格式不正确）
            related_snippet_idx_list = [i for i in range(len(snippet_list))]
            # 返回所有快照的索引作为默认选择
            # 这是一个安全的fallback策略，确保即使解析失败也能返回结果
        
        in_out = {"state": "choose_snippet", "input": {"question": query, "snippet_str": snippet_str, "temperature": temperature, "max_tokens":max_tokens}, \
                "output": snippet_list, "response": {"content":response, "reasoning_content": reasoning_content}, "user_prompt": user_prompt, "cost_time": str(round(time.time()-start_time, 3))}
        # 构建日志记录字典，包含完整的输入输出信息
        # 字典结构详解：
        # - state: 当前状态 "choose_snippet"，表示正在执行快照选择任务
        # - input: 输入参数
        #   * question: 用户问题
        #   * snippet_str: 所有快照的字符串形式
        #   * temperature: 温度参数
        #   * max_tokens: 最大token数
        # - output: 输出的快照列表（原始输入的快照列表）
        # - response: 模型响应
        #   * content: 模型的完整响应内容
        #   * reasoning_content: 模型的思考过程
        # - user_prompt: 构建的用户提示词
        # - cost_time: 执行时间（四舍五入到3位小数，单位：秒）
        
        model_logger.info(json.dumps(in_out, ensure_ascii=False))
        # 将日志字典转换为JSON格式并记录到日志中
        # ensure_ascii=False 确保中文字符正常显示，不会被转义为Unicode编码
        
        yield "answer", related_snippet_idx_list
        # 生成器yield，向调用者返回最终结果
        # 标签为 "answer"，内容为相关快照的索引列表
        # 例如：[0, 2, 4] 表示第0、2、4个快照与用户问题最相关