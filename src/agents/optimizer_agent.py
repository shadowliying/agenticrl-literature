# encoding: utf-8  # 指定文件编码为UTF-8，确保中文字符正确显示
import time  # 导入时间模块，用于统计运行耗时与性能分析
import json  # 导入JSON模块，用于将日志数据序列化为JSON字符串

from llms.base_llm import BaseLLM  # 导入大语言模型基类，统一约束LLM接口
from utils.logger import model_logger  # 导入模型日志记录器，用于记录输入输出与耗时
from .base_agent import BaseAgent  # 导入智能体基类，提供一致的Agent抽象
from .prompts.optimizer_agent_prompts import SYSTEM_PROMPT4_EN, SYSTEM_PROMPT4_ZH  # 导入中英文优化器系统提示词

class OptimizerAgent(BaseAgent):  # 定义优化器智能体类，负责对“全流程”进行优化
    def __init__(self, llm: BaseLLM, lang: str):  # 构造函数，接收LLM实例与语言标识
        self.llm = llm  # 保存LLM实例，后续用于流式对话
        self.lang = lang  # 保存当前语言（"zh" 或 "en"），用于选择对应提示词

    def run(self, query, temperature=0.3, max_tokens=2048): 
         # 主方法：对传入的流程描述进行优化

        start_time = time.time()  
        # 记录开始时间，用于计算本次优化的耗时
        user_prompt = ""  
        # 初始化用户提示词

        if self.lang == "en":  # 如果是英文模式
            system_prompt = SYSTEM_PROMPT4_EN  # 选择英文系统提示词
            user_prompt = f"""【Full Process】\n{query}\n"""  # 构造英文用户提示内容，携带“全流程”文本
        elif self.lang == "zh":  # 如果是中文模式
            system_prompt = SYSTEM_PROMPT4_ZH  # 选择中文系统提示词
            user_prompt = f"""【全流程】\n{query}\n"""  # 构造中文用户提示内容，携带“全流程”文本
            
        response = ""  
        # 用于累积LLM的最终回答内容
        reasoning_content = ""  
        # 用于保存LLM的思考过程（链路推理）

        for label, cont in self.llm.stream_chat(system_content=system_prompt, user_content=user_prompt, temperature=temperature, max_tokens=max_tokens, answer_sleep=0):  # 以流式方式与LLM交互
            if label == "think":  # 如果当前片段是“思考内容”
                reasoning_content = cont  # 记录思考过程，便于审计与调试
                yield label, reasoning_content  # 将思考过程立即向上游流出，提升交互体验
            else:  # 否则为普通回答内容
                response += cont  # 逐步拼接为完整回答

        optimize_process = response.split("】")[-1].strip()  
        # 从响应中提取“】”后面的优化结果主体，去掉首尾空白
        
        in_out = {"state": "optimize_search_process", "input": {"process":query, "lang":self.lang, "temperature":temperature, "max_tokens":max_tokens}, \
                "output": optimize_process, "response": {"content": response,"reasoning_content":reasoning_content}, "user_prompt": user_prompt, "cost_time": str(round(time.time()-start_time, 3))}  
        # 组织结构化日志数据，包含输入、输出、思考内容与耗时
        model_logger.info(json.dumps(in_out, ensure_ascii=False))  
        # 以JSON形式记录日志，ensure_ascii=False保证中文不转义
        yield "answer", optimize_process  
        # 以生成器形式返回最终优化后的流程文本