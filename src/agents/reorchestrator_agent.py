# encoding: utf-8  # 指定文件编码为UTF-8，确保中文字符正确显示
import time  # 导入时间模块，用于计算代码执行耗时，监控性能
import json  # 导入JSON模块，用于序列化日志数据为标准格式

from llms.base_llm import BaseLLM  # 导入大语言模型基类，提供统一的LLM接口
from utils.logger import model_logger  # 导入模型日志记录器，用于记录智能体的操作过程
from .base_agent import BaseAgent  # 导入智能体基类，定义智能体的通用接口和规范
from .prompts.reorchestrator_agent_prompts import SYSTEM_PROMPT3, SYSTEM_PROMPT3_EN, SYSTEM_PROMPT3_6, SYSTEM_PROMPT3_6_EN  
# 导入不同场景的系统提示词模板
from config import MAX_CONTEXT_LENGTH  # 导入上下文最大长度配置，用于控制输入文本长度

class ReorchestratorAgent(BaseAgent):  # 定义重编排器智能体类，继承自基础智能体类
    def __init__(self, llm: BaseLLM, lang: str):  # 构造函数，初始化重编排器智能体实例
        self.llm = llm  # 设置智能体使用的大语言模型实例，用于推理和生成
        self.lang = lang  # 设置智能体的工作语言（"zh"中文 或 "en"英文）
    
    def truncate_prompt(self, query, evidence_list, now_step, whole_step, user_prompt_tpl, max_input_length):  # 智能截断方法，处理超长输入文本
        is_truncated = False  
        # 初始化截断标志，用于标记是否发生了文本截断
        evidence = ""  
        # 初始化证据字符串，用于存储最终使用的证据内容
        user_prompt = user_prompt_tpl.format(query=query, evidence=evidence, now_step=now_step, whole_step=whole_step)  
        # 构建初始的用户提示词
        for idx in range(len(evidence_list)):  
            # 遍历证据列表，逐个添加证据直到达到长度限制
            tmp_evidence = "\n".join(evidence_list[:idx+1])  
            # 将当前索引之前的所有证据连接成字符串
            tmp_user_prompt = user_prompt_tpl.format(query=query, evidence=tmp_evidence, now_step=now_step, whole_step=whole_step)  
            # 构建包含当前证据的临时提示词
            if len(self.llm.tokenizer.tokenize(tmp_user_prompt)) > max_input_length:  
                # 使用分词器检查临时提示词的token长度是否超过限制
                is_truncated = True  
                # 标记发生了截断，表示无法包含所有证据
                break  # 跳出循环，使用上一次的合法提示词
            user_prompt = tmp_user_prompt  
            # 更新用户提示词为当前的临时提示词
            evidence = tmp_evidence  
            # 更新证据内容为当前的临时证据
        
        return is_truncated, evidence, user_prompt  # 返回截断标志、最终证据内容和用户提示词


    def postprocess(self, response_text):  
        # 后处理分发方法，根据语言选择对应的处理逻辑
        res = dict()  
        # 初始化结果字典，用于存储解析后的结构化数据
        if self.lang == "zh": 
             # 如果当前语言是中文
            res = self.postprocess_zh(response_text)  # 调用中文后处理方法
        elif self.lang == "en":  
            # 如果当前语言是英文
            res = self.postprocess_en(response_text)  # 调用英文后处理方法
        return res  # 返回处理后的结构化结果
    
    def postprocess_zh(self, response):  
        # 中文响应的后处理方法，解析LLM输出的结构化信息
        update_now_step = response.split("【修改全流程】")[0].split("【修改当前步骤】")[-1].strip()  
        # 提取"修改当前步骤"的内容，通过标记符号分割
        update_whole_step = response.split("【修改全流程】")[-1].strip()  
        # 提取"修改全流程"的内容，获取完整的流程调整建议
        if len(update_whole_step.split("【")) > 1: 
            # 处理重复标记的情况，防止解析错误
            update_whole_step = update_whole_step.split("【")[0]  
            # 只取第一个标记之前的内容，去除多余的标记符号

        res = {  
            # 构建结构化的结果字典
            "update_now_step": update_now_step,  
            # 当前步骤的修改建议
            "update_whole_step": update_whole_step,  
            # 整个流程的修改建议
        }
        return res  # 返回结构化的处理结果

    def postprocess_en(self, response):  
        # 英文响应的后处理方法，处理逻辑与中文版本相同但使用英文标记
        update_now_step = response.split("【Modify Entire Process】")[0].split("【Modify Current Step】")[-1].strip()  
        # 提取当前步骤修改内容，使用英文标记符号
        update_whole_step = response.split("【Modify Entire Process】")[-1].strip()  
        # 提取整个流程修改内容，使用英文标记符号
        if len(update_whole_step.split("【")) > 1: 
            # 处理重复标记的情况，确保解析的准确性
            update_whole_step = update_whole_step.split("【")[0]  
            # 去除多余的标记符号，保持内容的纯净性

        res = {  
            # 构建结构化的结果字典
            "update_now_step": update_now_step,  
            # 当前步骤的修改建议
            "update_whole_step": update_whole_step,  
            # 整个流程的修改建议
        }
        return res  # 返回结构化的处理结果

    def run(self, query, evidence_list, now_step, whole_step, temperature=0.7, max_tokens=2048, step_type="webSearch"):  # 主运行方法，执行重编排逻辑
        start_time = time.time()  
        # 记录开始时间，用于计算执行耗时和性能监控
        max_input_length = MAX_CONTEXT_LENGTH - max_tokens  
        # 计算最大输入长度，确保输入+输出不超过模型上下文限制
        system_prompt = ""  
        # 初始化系统提示词变量，用于存储角色设定和任务描述
        user_prompt_tpl = ""  
        # 初始化用户提示词模板，用于构建具体的输入格式
        if self.lang == "zh":  
            # 如果当前语言是中文
            if step_type == "webSearch":  
                # 如果当前步骤类型是网络搜索
                system_prompt = SYSTEM_PROMPT3  
                # 使用中文网络搜索场景的系统提示词
                user_prompt_tpl = """【用户问题】\n{query}\n【查询结果】\n{evidence}\n【当前步骤】\n{now_step}\n【全流程】\n{whole_step}\n"""  
                # 定义中文搜索结果的提示词模板
            else:
                # 如果当前步骤类型是其他类型（如代码执行）
                system_prompt = SYSTEM_PROMPT3_6  
                # 使用中文代码执行场景的系统提示词
                user_prompt_tpl = """【用户问题】\n{query}\n【执行结果】\n {evidence}\n【当前步骤】\n{now_step}\n【全流程】\n {whole_step}\n"""  
                # 定义中文执行结果的提示词模板
        elif self.lang == "en":  
            # 如果当前语言是英文
            if step_type == "webSearch":  
                # 如果当前步骤类型是网络搜索
                system_prompt = SYSTEM_PROMPT3_EN  
                # 使用英文网络搜索场景的系统提示词
                user_prompt_tpl = """【User Question】\n{query}\n【Search Results】\n{evidence}\n【Current Step】\n{now_step}\n【Entire Process】\n{whole_step}\n"""  
                # 定义英文搜索结果的提示词模板
            else:  
                # 如果当前步骤类型是其他类型
                system_prompt = SYSTEM_PROMPT3_6_EN  
                # 使用英文代码执行场景的系统提示词
                user_prompt_tpl = """【User Question】\n{query}\n【Execution Result】\n {evidence}\n【Current Step】\n{now_step}\n【Entire Process】\n {whole_step}\n"""  
                # 定义英文执行结果的提示词模板
        is_truncated, evidence, user_prompt = self.truncate_prompt(query, evidence_list, now_step, whole_step, user_prompt_tpl, max_input_length)  
        # 调用截断方法，处理超长文本
        response = ""  
        # 初始化响应累积变量，用于收集LLM的完整响应
        reasoning_content = ""  
        # 初始化推理内容变量，用于存储LLM的思考过程
        for label, cont in self.llm.stream_chat(system_content=system_prompt, user_content=user_prompt, temperature=temperature, max_tokens=max_tokens, answer_sleep=0):  
            # 流式调用LLM进行推理
            if label == "think":  
                # 如果当前输出是思考过程
                reasoning_content = cont  
                # 保存推理内容，记录智能体的决策过程
                yield label, reasoning_content  
                # 向调用者实时返回思考过程，提升用户体验
            else:  # 如果当前输出是正常回答内容
                response += cont  
                # 累积回答内容到响应变量中
        res = self.postprocess(response)  
        # 对LLM的完整响应进行后处理，提取结构化的修改建议
        in_out = {"state": "update_search_process", "input": {"question": query, "evidence": evidence, "now_step": now_step, "whole_step": whole_step, "temperature": temperature, "max_tokens": max_tokens}, \
                "output": res, "response": {"content": response, "reasoning_content": reasoning_content}, "user_prompt": user_prompt, "cost_time": str(round(time.time()-start_time, 3))}  
        # 构建完整的输入输出日志记录，用于追踪和分析
        model_logger.info(json.dumps(in_out, ensure_ascii=False))  
        # 将操作日志以JSON格式记录到日志文件中，确保中文字符正确显示
        yield "answer", res  # 向调用者返回最终的结构化结果，包含流程修改建议