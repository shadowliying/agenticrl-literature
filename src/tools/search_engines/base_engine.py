# encoding: utf-8
# 指定文件编码为UTF-8，确保支持中文字符和其他多字节字符的正确处理

from abc import ABC, abstractmethod
# 从abc模块导入ABC（Abstract Base Class）抽象基类和abstractmethod装饰器
# ABC提供了创建抽象基类的基础设施
# abstractmethod装饰器用于标记必须在子类中实现的抽象方法

class BaseEngine(ABC):
    # 定义搜索引擎抽象基类，继承自ABC
    # 这个基类定义了所有搜索引擎必须实现的标准接口
    # 采用模板方法模式，确保所有搜索引擎子类具有统一的方法签名

    @abstractmethod
    # 装饰器标记下面的方法为抽象方法
    # 任何继承BaseEngine的子类都必须实现这个方法，否则无法实例化
    def clean_text(self, input_text):
        # 抽象方法：文本清理功能
        # 参数 input_text: 需要清理的原始文本，通常包含HTML标签、特殊字符等
        # 返回值：清理后的纯文本
        # 不同搜索引擎可能有不同的文本清理需求（如HTML解析、字符转义等）
        pass
        # pass语句：抽象方法的占位符，表示方法体为空
        # 子类必须重写此方法提供具体实现

    @abstractmethod
    # 再次使用装饰器标记下面的方法为抽象方法
    def search_title_snippet(self, query):
        # 抽象方法：搜索功能的核心接口
        # 参数 query: 搜索查询字符串，用户输入的关键词或问题
        # 返回值：搜索结果，通常是包含标题、链接、摘要等信息的数据结构
        # 这是所有搜索引擎的主要功能接口，负责执行实际的搜索操作
        pass
        # pass语句：抽象方法的占位符
        # 子类必须根据各自的搜索API和数据格式提供具体实现