# encoding: utf-8
# 设置文件编码为UTF-8，确保中文注释正确显示

from abc import ABC, abstractmethod
# 从abc模块导入ABC(Abstract Base Class)和abstractmethod装饰器
# 用于定义抽象基类和抽象方法

class BaseLLM(ABC):
    # 定义BaseLLM抽象基类，继承自ABC
    # 这是所有大语言模型实现类的基类，定义了统一的接口规范
    # 确保所有LLM实现都遵循相同的方法签名

    @abstractmethod
    def stream_chat(self, system_content="", user_content="", *args, **kwargs):
        # 抽象方法：流式聊天接口
        # 参数:
        #   system_content: str - 系统提示词，定义AI的角色和行为
        #   user_content: str - 用户输入内容
        #   *args, **kwargs - 其他可变参数，如温度、最大token数等
        # 返回: generator - 流式生成器，逐步返回生成的内容
        # 用途: 实现实时流式输出，提升用户体验
        pass
        # 抽象方法必须在子类中实现
    
    @abstractmethod
    def chat(self, system_content="", user_content="", *args, **kwargs):
        # 抽象方法：非流式聊天接口
        # 参数:
        #   system_content: str - 系统提示词
        #   user_content: str - 用户输入内容
        #   *args, **kwargs - 其他可变参数
        # 返回: str - 完整的生成内容
        # 用途: 获取完整回答，适用于一次性获取结果的场景
        pass
        # 抽象方法必须在子类中实现