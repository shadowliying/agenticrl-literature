# encoding: utf-8
# 设置文件编码为UTF-8，确保中文配置项正确处理

import yaml
# 导入YAML解析库，用于读取和解析config.yml配置文件

import os
# 导入操作系统接口模块，用于处理文件路径和目录操作

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 获取项目根目录路径
# os.path.abspath(__file__): 获取当前文件的绝对路径
# os.path.dirname(): 第一次调用获取config目录路径
# os.path.dirname(): 第二次调用获取src目录路径（项目根目录）

RESOURCES_PATH = os.path.join(ROOT_PATH, 'resources')
# 构建资源文件目录路径，用于存放tokenizer等资源文件

with open(os.path.join(ROOT_PATH, 'config/config.yml'),'r', encoding='utf-8') as conf_file:
    # 打开配置文件，使用UTF-8编码确保中文配置项正确读取
    # os.path.join()用于构建跨平台兼容的文件路径
    config = yaml.safe_load(conf_file)
    # 使用yaml.safe_load()安全地加载YAML配置文件内容
    # safe_load比load更安全，可以防止执行恶意代码

service_name = "deepliterature"
# 定义服务名称，用于从配置文件中获取对应的配置节点

config = config[service_name]
# 从配置文件中提取deepliterature服务的配置信息

################# Language Configuration ###########################
# 语言配置节，设置系统的语言选项

LANGUAGE = config["language"]
# 从配置文件中读取语言设置，支持"zh"(中文)和"en"(英文)

################# llm Configuration ###########################
# 大语言模型配置节，包含模型相关的所有配置

LLM_CONFIG = config["llm"]
# 获取LLM配置字典，包含最大上下文长度、模型类型等信息

MAX_CONTEXT_LENGTH = LLM_CONFIG["max_context_length"]
# 设置大语言模型的最大上下文长度（输入+输出token总数）

LLM_MODEL =  LLM_CONFIG["llm_model"]
# 设置使用的LLM模型类型，可选："remote-llm"或"remote-reasoning-llm"

################# remote-llm Configuration ###########################
# 远程大语言模型配置节，用于配置标准的远程LLM服务

REMOTE_LLM_CONFIG = LLM_CONFIG["remote-llm"]
# 获取远程LLM的配置字典

REMOTE_LLM_API_URL = REMOTE_LLM_CONFIG["api_url"]
# 远程LLM服务的API接口地址

REMOTE_LLM_API_KEY = REMOTE_LLM_CONFIG["api_key"]
# 远程LLM服务的API密钥，用于身份验证

REMOTE_LLM_MODEL_NAME = REMOTE_LLM_CONFIG["model_name"]
# 远程LLM服务使用的具体模型名称

REMOTE_LLM_TOKENIZER_CONFIG = REMOTE_LLM_CONFIG["tokenizer"]
# 获取远程LLM的tokenizer配置信息

REMOTE_LLM_TOKENIZER_NAME_OR_PATH = REMOTE_LLM_TOKENIZER_CONFIG.get("tokenizer_name_or_path", "")
# 获取tokenizer的名称或路径，使用get()方法提供默认值""

REMOTE_LLM_TOKENIZER_CLASS = REMOTE_LLM_TOKENIZER_CONFIG["tokenizer_class"]
# 获取tokenizer的类名，用于动态加载对应的tokenizer类

################# remote-reasoning-llm Configuration ###########################
# 远程推理大语言模型配置节，用于配置具有推理能力的LLM服务（如DeepSeek-R1）

REMOTE_REASONING_LLM_CONFIG = LLM_CONFIG["remote-reasoning-llm"]
# 获取远程推理LLM的配置字典

REMOTE_REASONING_LLM_API_URL = REMOTE_REASONING_LLM_CONFIG["api_url"]
# 远程推理LLM服务的API接口地址

REMOTE_REASONING_LLM_API_KEY = REMOTE_REASONING_LLM_CONFIG["api_key"]
# 远程推理LLM服务的API密钥，用于身份验证

REMOTE_REASONING_LLM_MODEL_NAME = REMOTE_REASONING_LLM_CONFIG["model_name"]
# 远程推理LLM服务使用的具体模型名称

REMOTE_REASONING_LLM_TOKENIZER_CONFIG = REMOTE_REASONING_LLM_CONFIG["tokenizer"]
# 获取远程推理LLM的tokenizer配置信息

REMOTE_REASONING_LLM_TOKENIZER_NAME_OR_PATH = os.path.join(RESOURCES_PATH, REMOTE_REASONING_LLM_TOKENIZER_CONFIG.get("tokenizer_name_or_path", ""))
# 构建tokenizer资源文件的完整路径，将资源目录路径与tokenizer路径拼接

REMOTE_REASONING_LLM_TOKENIZER_CLASS = REMOTE_REASONING_LLM_TOKENIZER_CONFIG["tokenizer_class"]
# 获取推理LLM tokenizer的类名


################# search-engine Configuration ###########################
# 搜索引擎配置节，用于配置网络搜索功能

SEARCH_CONFIG = config["search-engine"]
# 获取搜索引擎配置字典

SEARCH_ENGINE = SEARCH_CONFIG["search_engine"]
# 设置使用的搜索引擎类型，当前支持"serp"(SerpApi)

################# search-serpapi Configuration ###########################
# SerpApi搜索服务配置节，SerpApi是Google搜索结果的API服务

SERPAPI_CONFIG = SEARCH_CONFIG["serp"]
# 获取SerpApi的配置字典

SERPAPI_URL = SERPAPI_CONFIG["api_url"]
# SerpApi服务的接口地址，通常为"https://serpapi.com/search"

SERPAPI_KEY = SERPAPI_CONFIG["api_key"]
# SerpApi服务的API密钥，用于访问搜索服务

SERPAPI_GL = SERPAPI_CONFIG["gl"]
# Google Location参数，指定搜索结果的地理位置（如"cn"表示中国）

SERPAPI_HL = SERPAPI_CONFIG["hl"]
# Google Language参数，指定搜索结果的语言（如"zh"表示中文）


################# jina Configuration ###########################
# Jina AI配置节，Jina提供文本embedding和网页内容提取服务

JINA_CONFIG = config["jina"]
# 获取Jina服务的配置字典

JINA_API_URL = JINA_CONFIG["api_url"]
# Jina API服务的接口地址，用于网页内容提取等功能

JINA_API_KEY = JINA_CONFIG["api_key"]
# Jina服务的API密钥，用于身份验证

################# code-runner Configuration ###########################
# 代码执行器配置节，用于配置远程代码执行服务

CODE_RUNNER_CONFIG = config["code-runner"]
# 获取代码执行器的配置字典

CODE_RUNNER_API_URL = CODE_RUNNER_CONFIG["api_url"]
# 代码执行服务的API接口地址，用于执行Python代码和生成图表等



