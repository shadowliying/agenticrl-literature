# encoding: utf-8
# 设置文件编码为UTF-8，确保中文注释正确显示

import requests
# 导入requests库，用于发送HTTP请求到远程LLM API

import traceback
# 导入traceback模块，用于打印详细的异常堆栈信息

import json
# 导入json模块，用于处理JSON格式的请求和响应数据

import time
# 导入time模块，用于控制流式输出的时间间隔


from config.config import REMOTE_LLM_API_URL, REMOTE_LLM_API_KEY, REMOTE_LLM_MODEL_NAME, LANGUAGE
# 从配置模块导入远程LLM相关配置:
# REMOTE_LLM_API_URL: API接口地址
# REMOTE_LLM_API_KEY: API访问密钥
# REMOTE_LLM_MODEL_NAME: 模型名称
# LANGUAGE: 系统语言设置

from utils.common_utils import get_real_time_str, get_location_by_ip
# 从工具模块导入实用函数:
# get_real_time_str(): 获取当前时间字符串
# get_location_by_ip(): 根据IP获取地理位置

from .base_llm import BaseLLM
# 导入基础LLM抽象类

class RemoteLLM(BaseLLM):
    # 定义远程LLM类，继承自BaseLLM抽象基类
    # 实现标准的远程大语言模型API调用功能
    
    def __init__(self, tokenizer=None, api_url=REMOTE_LLM_API_URL, api_key=REMOTE_LLM_API_KEY):
        # 构造函数，初始化远程LLM实例
        # 参数:
        #   tokenizer: 分词器实例，用于token计数和文本处理
        #   api_url: API接口地址，默认使用配置中的地址
        #   api_key: API访问密钥，默认使用配置中的密钥
        
        self.api_url = api_url
        # 存储API接口地址
        
        self.api_key = api_key
        # 存储API访问密钥
        
        self.tokenizer = tokenizer
        # 存储tokenizer实例

    def stream_chat(self, system_content="", user_content="", temperature=0.7, max_tokens=2048, answer_sleep=0.02):
        # 流式聊天方法，实现实时流式输出
        # 参数:
        #   system_content: str - 系统提示词，定义AI角色和行为
        #   user_content: str - 用户输入内容
        #   temperature: float - 生成温度，控制输出随机性(0-2)
        #   max_tokens: int - 最大输出token数
        #   answer_sleep: float - 流式输出的时间间隔，单位秒
        # 返回: generator - 生成器，逐步返回("answer", text)元组
        
        if len(system_content) == 0:
            # 如果没有提供系统提示词，使用默认提示词
            
            if LANGUAGE == "zh":
                # 中文环境下的默认系统提示词
                system_content = f"你的身份是一个友善且乐于助人的智能体(agent)。你需要把自己作为智能体和用户进行友善问答。当前的时间为{get_real_time_str()}。当前所在地: {get_location_by_ip()}。"
                
            elif LANGUAGE == "en":
                # 英文环境下的默认系统提示词
                system_content = f"Your identity is a friendly and helpful agent. You need to engage in friendly Q&A with users as a agent. The current time is{get_real_time_str()}. Current location: {get_location_by_ip()}."


        request_header = {
            # 构建HTTP请求头
            'Content-Type':'application/json',
            # 设置内容类型为JSON
            "Authorization": f"Bearer {self.api_key}"
            # 设置Bearer Token认证
        }

        request_json={
            # 构建请求体JSON数据
            "model":REMOTE_LLM_MODEL_NAME,
            # 指定使用的模型名称
            "messages":[
                # 消息列表，遵循OpenAI API格式
                {"role":"system", "content":system_content},
                # 系统消息，定义AI的角色和行为
                {"role":"user", "content":user_content},
                # 用户消息，包含用户的问题或指令
            ],
            "temperature" : temperature,
            # 设置生成温度
            "max_tokens" : max_tokens,
            # 设置最大输出token数
            "stream": True
            # 启用流式输出模式
        }

        try:
            # 尝试发送HTTP POST请求
            response = requests.post(self.api_url, headers=request_header, json=request_json)
        except Exception as e:
            # 捕获请求异常
            traceback.print_exc()
            # 打印详细的异常堆栈信息
            raise e
            # 重新抛出异常
            
        if response.status_code == 200:
            # 如果请求成功(HTTP 200)
            
            for line in response.iter_lines():
                # 逐行处理流式响应
                line = line.decode('utf-8').strip()
                # 解码并去除首尾空白
                
                if len(line) == 0:
                    # 跳过空行
                    continue
                    
                line = line.lstrip("data:").strip()
                # 去除SSE(Server-Sent Events)格式的"data:"前缀
                
                if line == "[DONE]":
                    # 检测到流式传输结束标记
                    break
                    
                data = json.loads(line)
                # 解析JSON响应数据
                # json是一个模块 它里面包括了一个loads的函数
                
                if "finish_reason" in data["choices"][0] and data["choices"][0]["finish_reason"] == "stop":
                    # 检查是否有完成原因且为"stop"，表示正常结束
                    break
                # 每次调用只生成一条回答；
                # 所以 choices 这个数组的长度固定是 1；
                # 那就没必要多此一举循环，直接访问 choices[0] 是最简单的写法。

                text = data["choices"][0]["delta"]["content"]
                # 提取当前步骤生成的内容

                if len(text) == 0:
                    # 跳过空内容
                    continue
                    
                yield "answer", text
                # 流式返回生成的内容，标签为"answer"
                
                if answer_sleep > 0:
                    # 如果设置了延迟时间
                    time.sleep(answer_sleep)
                    # 暂停指定时间，控制输出速度
        else:
            # 如果请求失败
            raise Exception(f"Error: {response.status_code} - {response.text}")
            # 抛出包含状态码和错误信息的异常


    def chat(self, system_content="", user_content="", temperature=0.7, max_tokens=2048):
        # 非流式聊天方法，一次性返回完整结果
        # 参数: 与stream_chat相同，但没有answer_sleep参数
        # 返回: str - 完整的生成内容
        
        if len(system_content) == 0:
            # 如果没有提供系统提示词，使用默认提示词
            
            if LANGUAGE == "zh":
                # 中文默认系统提示词
                system_content = f"你的身份是一个友善且乐于助人的智能体(agent)。你需要把自己作为智能体和用户进行友善问答。当前的时间为{get_real_time_str()}。当前所在地: {get_location_by_ip()}。"
                
            elif LANGUAGE == "en":
                # 英文默认系统提示词
                system_content = f"Your identity is a friendly and helpful agent. You need to engage in friendly Q&A with users as a agent. The current time is{get_real_time_str()}. Current location: {get_location_by_ip()}."


        request_header = {
            # 构建HTTP请求头
            'Content-Type':'application/json',
            "Authorization": f"Bearer {self.api_key}"
        }

        request_json={
            # 构建请求体，注意这里模型名称被硬编码了
            "model":"gpt-4o-2024-08-06",
            # 注意：这里应该使用REMOTE_LLM_MODEL_NAME配置，存在潜在的配置不一致问题
            "messages":[
                {"role":"system", "content":system_content},
                {"role":"user", "content":user_content},
            ],
            "temperature" : temperature,
            "max_tokens" : max_tokens,
            # 注意：非流式模式不设置stream参数，默认为False
        }

        try:
            # 尝试发送HTTP POST请求
            response = requests.post(self.api_url, headers=request_header, json=request_json)
        except:
            # 捕获所有异常，返回错误信息
            return "Error: 404 - None"
            
        if response.status_code == 200:
            # 如果请求成功
            response_content = ""
            # 初始化响应内容字符串
            
            for line in response.iter_lines():
                # 逐行读取响应内容
                response_content += line.decode('utf-8') + "\n"
                # 拼接所有行内容
                
            return json.loads(response_content)["choices"][0]["message"]["content"]
            # 解析JSON响应并返回消息内容
        else:
            # 如果请求失败
            return f"Error: {response.status_code} - {response.text}"
            # 返回错误信息