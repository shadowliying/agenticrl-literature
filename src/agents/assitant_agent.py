# encoding: utf-8
# 设置文件编码为 UTF-8，确保中文字符正确显示

import time
# 导入时间模块，用于计算任务执行时间

import json
# 导入 JSON 模块，用于序列化日志数据


from llms.base_llm import BaseLLM
# 从 llms.base_llm 模块导入 BaseLLM 基类，这是所有大语言模型的基础接口

from utils.logger import model_logger
# 从 utils.logger 模块导入 model_logger，用于记录模型运行日志

from .base_agent import BaseAgent
# 从当前包的 base_agent 模块导入 BaseAgent 基类，所有智能体的基础类

from .prompts.assitant_agent_prompts import SYSTEM_PROMPT6, SYSTEM_PROMPT6_EN
# 从 prompts.assitant_agent_prompts 模块导入系统提示词，包括中文和英文版本

from config import MAX_CONTEXT_LENGTH
# 从 config 模块导入最大上下文长度配置

class AssitantAgent(BaseAgent):
    # 定义 AssitantAgent 类，继承自 BaseAgent 基类
    # 这是一个助手智能体，用于根据搜索结果和代码执行结果生成最终答案
    
    def __init__(self, llm: BaseLLM, lang: str):
        # 构造函数，初始化助手智能体
        # 参数:
        #   llm: BaseLLM - 大语言模型实例，用于生成回答
        #   lang: str - 语言设置，支持 "zh"(中文) 或 "en"(英文)
        
        self.llm = llm
        # 存储大语言模型实例
        
        self.lang = lang
        # 存储语言设置

    def run(self, query, search_process, evidence_list, code_evidence_list, temperature=1, max_tokens=4096):
        # 运行助手智能体的主要方法，生成基于搜索结果的最终答案
        # 参数:
        #   query: str - 用户的原始问题
        #   search_process: str - 搜索过程的描述信息
        #   evidence_list: list - 搜索到的相关证据列表
        #   code_evidence_list: list - 代码执行结果的证据列表
        #   temperature: float - 生成温度，控制输出的随机性，默认为1
        #   max_tokens: int - 最大输出token数量，默认为4096
        # 返回: generator - 流式返回生成的内容
        
        start_time = time.time()
        # 记录开始时间，用于计算执行耗时
        
        code_evidence = ""
        # 初始化代码证据字符串
        
        user_prompt = ""
        # 初始化用户提示词
        
        system_prompt = ""
        # 初始化系统提示词
        
        if self.lang == "zh":
            # 如果语言设置为中文
            
            if len(code_evidence_list) > 0:
                # 如果有代码证据列表不为空
                code_evidence = '\n'.join(code_evidence_list)
                # 将代码证据列表用换行符连接成字符串
            else:
                # 如果没有代码证据
                code_evidence = "无需代码"
                # 设置为"无需代码"
                
            user_prompt = f"【问题】{query}\n【搜索过程】{search_process}【代码结果】\n{code_evidence}\n【相关内容】\n"
            # 构建中文用户提示词，包含问题、搜索过程、代码结果等部分
            
            system_prompt = SYSTEM_PROMPT6
            # 使用中文系统提示词
            
        elif self.lang == "en":
            # 如果语言设置为英文
            
            if len(code_evidence_list) > 0:
                # 如果有代码证据列表不为空
                code_evidence = '\n'.join(code_evidence_list)
                # 将代码证据列表用换行符连接成字符串
            else:
                # 如果没有代码证据
                code_evidence = "No code is needed."
                # 设置为英文"No code is needed."
                
            user_prompt = f"【Question】{query}\n【Search Process】{search_process}【Code Results】\n{code_evidence}\n【Relevant Content】\n"
            # 构建英文用户提示词，包含问题、搜索过程、代码结果等部分
            
            system_prompt = SYSTEM_PROMPT6_EN
            # 使用英文系统提示词

        max_input_length = MAX_CONTEXT_LENGTH - max_tokens
        # 计算最大输入长度，为总长度减去最大输出token数，预留输出空间
        
        for idx in range(len(evidence_list)):
            # 遍历证据列表的索引
            
            evidence = evidence_list[idx] + "\n"
            # 获取当前证据并添加换行符
            
            if len(self.llm.tokenizer.tokenize(user_prompt + evidence)) > max_input_length:
                # 如果添加当前证据后的总token数超过最大输入长度
                break
                # 跳出循环，避免超出上下文限制
                
            user_prompt += evidence
            # 将当前证据添加到用户提示词中

        
        has_cutted = False
        # 标记是否已经截取了答案部分，用于去除答案前的无关内容
        
        response =  ""
        # 初始化完整响应内容
        
        reasoning_content = ""
        # 初始化推理内容（当前版本中未使用）
        
        llm_answer = ""
        # 初始化LLM的答案内容
        
        for label, cont in self.llm.stream_chat(system_prompt, user_prompt, temperature, max_tokens, answer_sleep=0):
            # 调用LLM的流式聊天方法，逐步生成回答
            # label: 内容标签，可能是 "think"(思考过程) 或其他(实际回答)
            # cont: 当前生成的内容片段
            
            if label == "think":
                # 如果是思考过程内容
                yield label, cont
                # 直接流式返回思考内容
            else:
                # 如果是实际回答内容
                response += cont
                # 将内容添加到完整响应中
                
                llm_answer += cont
                # 将内容添加到LLM答案中
                
                if not has_cutted:
                    # 如果还没有截取答案部分
                    
                    if self.lang == "zh":
                        # 中文模式下
                        if "【答案】" in llm_answer:
                            # 如果检测到【答案】标记
                            llm_answer = llm_answer.split("【答案】")[-1].strip()
                            # 截取【答案】后面的内容作为最终答案
                            has_cutted = True
                            # 标记已经截取
                            
                    elif self.lang == "en":
                        # 英文模式下
                        if "【Answer】" in llm_answer:
                            # 如果检测到【Answer】标记
                            llm_answer = llm_answer.split("【Answer】")[-1].strip()
                            # 截取【Answer】后面的内容作为最终答案
                            has_cutted = True
                            # 标记已经截取
                            
                yield label, cont
                # 流式返回当前内容片段

        in_out = {"state": "create_answer", "input": {"question": query, "search_process": search_process, "evidence_list": evidence_list, "code_evidence_list":code_evidence_list,"temperature": temperature, "max_tokens":max_tokens}, \
                "output": llm_answer, "response": {"content":response, "reasoning_content": reasoning_content}, "user_prompt": user_prompt, "cost_time": str(round(time.time()-start_time, 3))}
        # 构建输入输出日志字典，包含：
        # - state: 当前状态为"create_answer"
        # - input: 输入参数，包括问题、搜索过程、证据列表、温度、最大token数等
        # - output: 最终答案
        # - response: 响应信息，包括完整内容和推理内容
        # - user_prompt: 用户提示词
        # - cost_time: 执行耗时（秒）
        
        model_logger.info(json.dumps(in_out, ensure_ascii=False))
        # 将日志信息序列化为JSON格式并记录到模型日志中，ensure_ascii=False确保中文正确显示
