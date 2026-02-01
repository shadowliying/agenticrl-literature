# encoding: utf-8
# 文件编码声明，指定使用 UTF-8 编码格式

import time
# 导入时间模块，用于计算代码执行时间

import json
# 导入 JSON 模块，用于记录日志时将数据序列化为 JSON 格式

from llms.base_llm import BaseLLM
# 从 llms.base_llm 模块导入 BaseLLM 基础大语言模型类

from utils.logger import model_logger
# 从 utils.logger 模块导入 model_logger，用于记录模型运行日志

from .base_agent import BaseAgent
# 从当前包的 base_agent 模块导入 BaseAgent 基础智能体类

from .prompts.code_agent_prompts import SYSTEM_PROMPT3_3, SYSTEM_PROMPT3_3_EN
# 从 prompts.code_agent_prompts 模块导入中文和英文的系统提示词

from config import MAX_CONTEXT_LENGTH
# 从 config 模块导入最大上下文长度常量

class CodeAgent(BaseAgent):
    # 定义 CodeAgent 类，继承自 BaseAgent 基础智能体类
    # 这是一个专门用于生成和执行代码的智能体
    
    def __init__(self, llm: BaseLLM, lang:str):
        # 构造函数，初始化 CodeAgent 实例
        # 参数：
        # - llm: BaseLLM 类型，大语言模型实例
        # - lang: str 类型，语言设置（"zh" 表示中文，"en" 表示英文）
        
        self.llm = llm
        # 将传入的大语言模型实例赋值给实例变量 self.llm
        
        self.lang = lang
        # 将传入的语言设置赋值给实例变量 self.lang

    def run(self, query, now_code_step, previous_reference, reference_list, temperature=0.7, max_tokens=2048):
        # 定义 run 方法，这是 CodeAgent 的主要执行方法
        # 参数：
        # - query: 用户提出的问题
        # - now_code_step: 当前需要执行的代码步骤
        # - previous_reference: 之前的参考信息
        # - reference_list: 参考信息列表
        # - temperature: 温度参数，控制生成文本的随机性，默认 0.7
        # - max_tokens: 最大生成 token 数量，默认 2048
        
        start_time = time.time()
        # 记录开始时间，用于计算整个方法的执行时长
        
        max_input_length = MAX_CONTEXT_LENGTH - max_tokens
        # 计算最大输入长度 = 最大上下文长度 - 最大输出 token 数
        # 确保输入和输出的总长度不超过模型的上下文限制
        
        cur_references = [previous_reference]
        # 初始化当前参考信息列表，先添加之前的参考信息
        
        reference_doc = "\n".join(cur_references)
        # 将当前参考信息列表用换行符连接成一个字符串
        
        user_prompt_tpl = ""
        # 初始化用户提示词模板变量
        
        system_prompt = ""
        # 初始化系统提示词变量
        
        if self.lang == "zh":
            # 如果语言设置为中文
            user_prompt_tpl = "【用户问题】\n{query}\n【当前步骤】\n{now_code_step}\n【参考信息】{reference_doc}\n【执行代码】\n"
            # 设置中文的用户提示词模板，包含用户问题、当前步骤、参考信息等部分
            system_prompt = SYSTEM_PROMPT3_3
            # 使用中文的系统提示词
        elif self.lang == "en":
            # 如果语言设置为英文
            user_prompt_tpl = "【Question】\n{query}\n【Current Step】\n{now_code_step}\n【Reference Information】{reference_doc}\n【Execution Code】\n"
            # 设置英文的用户提示词模板，包含问题、当前步骤、参考信息等部分
            system_prompt = SYSTEM_PROMPT3_3_EN
            # 使用英文的系统提示词
            
        user_prompt = user_prompt_tpl.format(query=query, now_code_step=now_code_step, reference_doc=reference_doc)
        # 使用模板格式化生成完整的用户提示词，填入实际的查询、步骤和参考信息
        
        for ref in reference_list:
            # 遍历参考信息列表中的每个参考信息
            cur_references.append(ref)
            # 将当前参考信息添加到当前参考列表中
            tmp_ref_doc = "\n".join(cur_references)
            # 将更新后的参考信息列表连接成字符串
            tmp_user_prompt = user_prompt_tpl.format(query=query, now_code_step=now_code_step, reference_doc=tmp_ref_doc)
            # 生成包含新参考信息的临时用户提示词
            if len(self.llm.tokenizer.tokenize(tmp_user_prompt)) > max_input_length:
                # 如果临时提示词的 token 长度超过最大输入长度限制
                break
                # 跳出循环，不再添加更多参考信息
            reference_doc = tmp_ref_doc
            # 更新参考文档为临时参考文档
            user_prompt = tmp_user_prompt
            # 更新用户提示词为临时用户提示词
            
        response = ""
        # 初始化响应字符串，用于累积模型的输出内容
        
        reasoning_content = ""
        # 初始化推理内容字符串，用于累积模型的思考过程
        
        for label, cont in self.llm.stream_chat(system_content=system_prompt, user_content=user_prompt, temperature=temperature, max_tokens=max_tokens):
            # 调用大语言模型的流式聊天方法，传入系统提示词、用户提示词、温度和最大 token 数
            # 返回标签和内容的迭代器
            if label == "think":
                # 如果标签是 "think"，表示这是模型的思考过程
                reasoning_content += cont
                # 将内容添加到推理内容中
            else:
                # 如果标签不是 "think"，表示这是模型的正式响应
                response += cont
                # 将内容添加到响应中
            yield label, cont
            # 生成器yield，向调用者返回标签和内容
            
        cleaned_text = response.strip()
        # 去除响应文本前后的空白字符
        
        lines = cleaned_text.splitlines()
        # 将清理后的文本按行分割成列表
        
        start_line = 0
        # 初始化代码块开始行号
        
        end_line = len(lines) - 1
        # 初始化代码块结束行号为最后一行
        
        for line_idx, line in enumerate(lines):
            # 遍历每一行，查找代码块的开始位置
            if line.startswith("```python"):
                # 如果行以 "```python" 开头，表示这是 Python 代码块的开始
                start_line = line_idx
                # 记录开始行号
                break
                # 跳出循环
            if line.startswith("```"):
                # 如果行以 "```" 开头，表示这是代码块的开始（通用格式）
                start_line = line_idx
                # 记录开始行号
                break
                # 跳出循环

        while end_line > 0:
            # 从后往前查找代码块的结束位置
            if lines[end_line].startswith("```"):
                # 如果行以 "```" 开头，表示这是代码块的结束
                break    
                # 跳出循环
            end_line -= 1
            # 向前移动一行

        in_out = {"state": "creat_code", "input": {"question": query, "now_code_step": now_code_step, "reference_doc": reference_doc,"temperature": temperature, "max_tokens":max_tokens}, \
                "output": lines, "response": {"content":response, "reasoning_content": reasoning_content}, "user_prompt": user_prompt, "cost_time": str(round(time.time()-start_time, 3))}
        # 构建日志记录字典，包含：
        # - state: 当前状态 "creat_code"
        # - input: 输入参数（问题、当前步骤、参考文档、温度、最大token数）
        # - output: 输出的代码行列表
        # - response: 响应内容（包含正式回答和推理过程）
        # - user_prompt: 用户提示词
        # - cost_time: 执行时间（四舍五入到3位小数）
        
        model_logger.info(json.dumps(in_out, ensure_ascii=False))
        # 将日志字典转换为JSON格式并记录到日志中，ensure_ascii=False确保中文字符正常显示

        if start_line < end_line:
            # 如果找到了有效的代码块（开始行小于结束行）
            yield "final_answer", "\n".join(lines[start_line + 1:end_line])
            # 提取代码块内容（去除代码块标记行），用换行符连接并作为最终答案返回
        else:
            # 如果没有找到有效的代码块
            yield "final_answer", "\n".join(lines)
            # 返回所有行作为最终答案
        
