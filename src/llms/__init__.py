# encoding: utf-8
# LLMs模块初始化文件
# 该模块负责大语言模型(Large Language Models)的封装和管理
# 提供统一的LLM接口，支持多种远程LLM服务

from .remote_llm import RemoteLLM
# 导入标准远程LLM类，用于调用常规的大语言模型API服务
# 如OpenAI GPT、Claude、国产大模型等

from .remote_reasoning_llm import RemoteReasoningLLM
# 导入具有推理能力的远程LLM类，用于调用支持Chain-of-Thought推理的模型
# 如DeepSeek-R1等具有显式推理过程的模型

from .llm_factory import LLMFactory
# 导入LLM工厂类，提供统一的LLM实例创建接口
# 根据配置自动选择和创建对应的LLM实例