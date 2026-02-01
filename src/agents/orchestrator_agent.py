# encoding: utf-8  # 指定文件编码为UTF-8，确保中文字符正确显示
import time  # 导入时间模块，用于计算代码执行耗时
import re  # 导入正则表达式模块，用于从LLM响应中提取特定格式的函数调用
import json  # 导入JSON模块，用于序列化日志数据

from llms.base_llm import BaseLLM  # 导入大语言模型基类，提供LLM接口
from utils.logger import model_logger  # 导入模型日志记录器，用于记录操作日志
from .base_agent import BaseAgent  # 导入智能体基类，定义智能体通用接口
from .prompts.orchestrator_agent_prompts import SYSTEM_PROMPT_ZH, SYSTEM_PROMPT_EN  # 导入中英文系统提示词


'''
（编排器智能体）- 核心调度器
核心功能:
    解析用户查询，判断任务类型  # 分析用户输入，确定需要什么类型的处理
    决定是否需要搜索/代码执行  # 智能判断是否需要进行网络搜索或代码执行
    生成搜索关键词  # 从用户查询中提取或生成有效的搜索关键词
    制定执行策略  # 确定任务执行的步骤和策略（单步、并发、多步等）
'''

class OrchestratorAgent(BaseAgent):  
    # 定义编排器智能体类，继承自基础智能体类
    def __init__(self, llm: BaseLLM, lang: str):  
        # 构造函数，初始化智能体实例
        self.llm = llm  
        # 设置智能体使用的大语言模型实例
        self.lang = lang  
        # 设置智能体的工作语言（"zh"中文 或 "en"英文）

    @staticmethod  
    # 静态方法装饰器，该方法不依赖实例状态，可直接通过类调用
    def parse_keywords(text):   
        # 定义关键词解析方法，从LLM输出中提取函数调用格式的关键词
        pattern = r'webSearch\("([^"]+)"\)' 
        # 定义正则表达式模式，匹配webSearch("关键词")格式
        matches1 = re.findall(pattern, text)  
        # 使用正则表达式查找所有匹配的网络搜索关键词
        pattern2 = r'codeRunner\("([^"]+)"\)'  
        # 定义正则表达式模式，匹配codeRunner("代码")格式
        matches2 = re.findall(pattern2, text)  
        # 使用正则表达式查找所有匹配的代码执行内容
        matches = []  
        # 初始化结果列表，用于存储所有提取到的关键词
        if matches2:  
            # 如果找到代码执行相关的匹配项
            matches.extend(matches2)  
            # 将代码执行关键词添加到结果列表中
        if matches1:  
            # 如果找到网络搜索相关的匹配项
            matches.extend(matches1)  
            # 将网络搜索关键词添加到结果列表中
        return matches  
        # 返回提取到的所有关键词列表
    
    def postprocess(self, response_text):  
        # 后处理方法，根据语言选择对应的处理逻辑
        res = dict()  
        # 初始化结果字典，用于存储解析后的结构化数据
        if self.lang == "zh":  
            # 如果当前语言是中文
            res = self.postprocess_zh(response_text)  
            # 调用中文后处理方法
        elif self.lang == "en":  
            # 如果当前语言是英文
            res = self.postprocess_en(response_text) 
             # 调用英文后处理方法
        return res  
        # 返回处理后的结构化结果
    
    def postprocess_zh(self, response_text):  
        # 中文响应的后处理方法
        keyword_list = OrchestratorAgent.parse_keywords(response_text)  
        # 调用静态方法提取关键词列表

        if_search = response_text.split("【搜索类型】")[0].split("【是否搜索】")[-1].strip()  
        # 提取"是否需要搜索"的判断结果
        search_type= response_text.split("【是否执行代码】")[0].split("【搜索类型】")[-1].strip()  
        # 提取"搜索类型"信息
        if_code = response_text.split("【执行过程】")[0].split("【是否执行代码】")[-1].strip()  
        # 提取"是否需要执行代码"的判断结果
        search_process = response_text.split("【执行过程】")[-1].strip()  
        # 提取"执行过程"的详细描述

        
        if len(keyword_list) > 1 and search_type == "单步单次":  
            # 如果关键词数量大于1且搜索类型是"单步单次"
            search_type = "单步并发"  
            # 自动调整为"单步并发"模式，提高效率
        if if_code not in ['是', '否']:  
            # 如果代码执行判断不是标准的"是"或"否"
            if_code = '否'  
            # 默认设置为"否"，即不执行代码
        if if_search not in ['是', '否']:  
            # 如果搜索判断不是标准的"是"或"否"
            if_search = '否'  
            # 默认设置为"否"，即不进行搜索
        res = {  
            # 构建结构化的结果字典
            "keyword_list": keyword_list, # 对于问题拆分的关键词list
            "if_search": if_search, # 是否需要检索的判定
            "if_code": if_code, # 是否需要执行代码
            "search_type": search_type, # 检索的类型：单步单次，单步并发，多步多次
            "search_process": search_process # 预设的检索过程
        }
        return res  # 返回结构化的处理结果

    def postprocess_en(self, response_text):  
        # 英文响应的后处理方法
        keyword_list = OrchestratorAgent.parse_keywords(response_text)  
        # 调用静态方法提取关键词列表
        if_search = response_text.split("【Search Type】")[0].split("【Search Required】")[-1].strip().lower()  
        # 提取搜索需求判断并转为小写
        search_type= response_text.split("【Code Execution Required】")[0].split("【Search Type】")[-1].strip() 
        # 提取搜索类型信息
        if_code = response_text.split("【Execution Process】")[0].split("【Code Execution Required】")[-1].strip().lower()  
        # 提取代码执行需求并转为小写
        search_process = response_text.split("【Execution Process】")[-1].strip()  
        # 提取执行过程描述
        if len(keyword_list) > 1 and search_type == "Single-step Single-search":  
            # 如果关键词数量大于1且为单步单搜索
            search_type = "Single-step Concurrent"  
            # 自动调整为单步并发模式
        if str(if_code) not in ['yes', 'no']:  
            # 如果代码执行判断不是标准的"yes"或"no"
            if_code = 'no'  
            # 默认设置为"no"，即不执行代码
        if str(if_search) not in ['yes', 'no']:  
            # 如果搜索判断不是标准的"yes"或"no"
            if_search = 'no'  
            # 默认设置为"no"，即不进行搜索
        res = {  
            # 构建结构化的结果字典
            "keyword_list": keyword_list, 
            # 对于问题拆分的关键词list
            "if_search": if_search, 
            # 是否需要检索的判定
            "if_code": if_code, 
            # 是否需要执行代码
            "search_type": search_type, 
            # 检索的类型：单步单次，单步并发，多步多次
            "search_process": search_process 
            # 预设的检索过程
        }
        return res  # 返回结构化的处理结果

    def run(self, query, temperature=0.3, max_tokens=2048):  
        # 主运行方法，处理用户查询
        start_time = time.time()  
        # 记录开始时间，用于计算执行耗时
        user_prompt = ""  
        # 初始化用户提示词变量
        systen_prompt = ""  
        # 初始化系统提示词变量（注意：这里可能是拼写错误，应为system_prompt）
        
        if self.lang == "zh":  # 如果当前语言是中文
            user_prompt = f"【问题】\n{query}"  # 构建中文格式的用户提示词
            systen_prompt = SYSTEM_PROMPT_ZH  # 使用中文系统提示词
        elif self.lang == "en":  # 如果当前语言是英文
            user_prompt = f"【Question】\n{query}"  # 构建英文格式的用户提示词
            systen_prompt = SYSTEM_PROMPT_EN  # 使用英文系统提示词
        
        now_keyword = ""  # 初始化关键词累积变量，用于收集LLM的完整响应
        reasoning_content = ""  # 初始化推理内容变量，用于存储思考过程

        for label, cont in self.llm.stream_chat(systen_prompt, user_prompt, temperature, max_tokens, answer_sleep=0):  
            # 流式调用LLM
            # 因为这个方法返回的是元组 第一个是label 第二个是内容
            if label == "think":  # 如果当前输出是思考过程
                reasoning_content = cont  # 保存推理内容
                yield label, reasoning_content  # 向调用者返回思考过程
            else:  # 如果当前输出是正常回答内容
                now_keyword += cont  # 累积回答内容到关键词变量中
        
        res = self.postprocess(now_keyword)  
        # 对LLM的完整响应进行后处理，提取结构化信息
        in_out = {"state": "query_classify", "input": {"question": query, "temperature": temperature, "max_tokens": max_tokens}, \
                "output": res, "response": {"content": now_keyword, "reasoning_content": reasoning_content}, "user_prompt": user_prompt, "cost_time": str(round(time.time()-start_time, 3))}  
        # 构建完整的输入输出日志记录
        model_logger.info(json.dumps(in_out, ensure_ascii=False))  
        # 将操作日志以JSON格式记录到日志文件中
        yield "answer", res  # 向调用者返回最终的结构化结果