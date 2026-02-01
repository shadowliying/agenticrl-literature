# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

from abc import ABC, abstractmethod
# 从abc模块导入ABC（Abstract Base Class）抽象基类和abstractmethod装饰器
# ABC提供了创建抽象基类的基础设施
# abstractmethod装饰器用于标记必须在子类中实现的抽象方法

class BaseTokenizer(ABC):
    # 定义分词器抽象基类，继承自ABC
    # 这个基类定义了所有分词器必须实现的标准接口
    # 采用模板方法模式，确保所有分词器子类具有统一的方法签名
    # 分词器用于将文本转换为token序列，是自然语言处理的基础步骤
    
    @abstractmethod
    # 装饰器标记下面的方法为抽象方法
    # 任何继承BaseTokenizer的子类都必须实现这个方法，否则无法实例化
    def tokenize(self, text):
        # 抽象方法：文本分词功能
        # 参数text: 需要进行分词的原始文本字符串
        # 返回值: token序列，通常是整数列表（token ID）或字符串列表（token文本）
        # 不同的分词器可能有不同的实现方式和返回格式
        pass
        # pass语句：抽象方法的占位符，表示方法体为空
        # 子类必须重写此方法提供具体的分词实现