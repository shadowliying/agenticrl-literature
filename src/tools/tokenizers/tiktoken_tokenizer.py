# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

import tiktoken
# 导入tiktoken库，这是OpenAI开发的高效分词器
# tiktoken主要用于GPT系列模型的文本预处理
# 它能够精确计算文本在特定模型中的token数量

from .base_tokenizer import BaseTokenizer
# 从同级目录导入BaseTokenizer抽象基类
# 使用相对导入确保模块间依赖关系正确


class TikTokenTokenizer(BaseTokenizer):
    # 定义TikTokenTokenizer类，继承自BaseTokenizer抽象基类
    # 实现基于tiktoken库的分词功能
    # 主要用于OpenAI GPT系列模型的文本处理
    
    def __init__(self, model_name):
        # 构造函数，初始化tiktoken分词器
        # 参数model_name: 模型名称，如"gpt-3.5-turbo"、"gpt-4"等
        # 不同模型使用不同的编码方式，需要指定具体模型名称
        
        self.enc = tiktoken.encoding_for_model(model_name)
        # 根据模型名称获取对应的编码器实例
        # tiktoken.encoding_for_model()会返回指定模型的官方编码器
        # 这确保了分词结果与模型实际使用的编码完全一致
        # 编码器包含了词汇表、特殊token等模型特定的信息

    def tokenize(self, text):
        # 实现父类的抽象方法tokenize，执行文本分词
        # 参数text: 需要分词的文本字符串
        # 返回值: token ID列表，每个ID对应词汇表中的一个token
        
        return self.enc.encode(text)
        # 使用tiktoken编码器将文本转换为token ID序列
        # encode()方法将文本按照模型的分词规则进行切分
        # 返回整数列表，每个整数是词汇表中token的唯一标识符
        # 这些token ID可以直接用于模型的输入处理