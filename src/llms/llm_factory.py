# encoding: utf-8
# 设置文件编码为UTF-8，确保中文注释正确显示

from typing import Literal
# 从typing模块导入Literal类型注解，用于限制参数的可选值

import importlib
# 导入importlib模块，用于动态导入模块和获取类

from .remote_llm import RemoteLLM
# 导入标准远程LLM类

from .remote_reasoning_llm import RemoteReasoningLLM
# 导入推理远程LLM类

from config import REMOTE_LLM_TOKENIZER_NAME_OR_PATH, REMOTE_LLM_TOKENIZER_CLASS, REMOTE_REASONING_LLM_TOKENIZER_NAME_OR_PATH, REMOTE_REASONING_LLM_TOKENIZER_CLASS
# 从配置模块导入tokenizer相关配置
# REMOTE_LLM_TOKENIZER_NAME_OR_PATH: 标准LLM的tokenizer路径
# REMOTE_LLM_TOKENIZER_CLASS: 标准LLM的tokenizer类名
# REMOTE_REASONING_LLM_TOKENIZER_NAME_OR_PATH: 推理LLM的tokenizer路径
# REMOTE_REASONING_LLM_TOKENIZER_CLASS: 推理LLM的tokenizer类名


class LLMFactory(object):
    # 定义LLM工厂类，采用工厂设计模式
    # 负责根据配置创建和初始化不同类型的LLM实例
    # 隐藏了复杂的实例化逻辑，提供简洁的创建接口
    
    @staticmethod
    def construct(model_name:Literal["remote-llm", "remote-reasoning-llm"]):
        # 静态方法：构造LLM实例
        # 参数:
        #   model_name: Literal - 模型类型，只能是"remote-llm"或"remote-reasoning-llm"
        # 返回: BaseLLM - 对应的LLM实例
        
        llm = None
        # 初始化LLM实例变量
        
        if model_name == "remote-llm":
            # 如果选择标准远程LLM
            
            tokenizer = getattr(importlib.import_module("tools.tokenizers"), REMOTE_LLM_TOKENIZER_CLASS)(REMOTE_LLM_TOKENIZER_NAME_OR_PATH)
            # 动态创建tokenizer实例的过程:
            # 1. importlib.import_module("tools.tokenizers"): 动态导入tokenizers模块
            # 2. getattr(module, class_name): 从模块中获取指定类名的类
            # 3. (path): 用路径参数实例化tokenizer类
            
            llm = RemoteLLM(tokenizer=tokenizer)
            # 创建RemoteLLM实例，传入配置好的tokenizer
            
        elif model_name == "remote-reasoning-llm":
            # 如果选择推理远程LLM
            
            tokenizer = getattr(importlib.import_module("tools.tokenizers"), REMOTE_REASONING_LLM_TOKENIZER_CLASS)(REMOTE_REASONING_LLM_TOKENIZER_NAME_OR_PATH)
            # 动态创建推理LLM对应的tokenizer实例
            
            llm = RemoteReasoningLLM(tokenizer=tokenizer)
            # 创建RemoteReasoningLLM实例，传入配置好的tokenizer
            
        return llm
        # 返回创建好的LLM实例