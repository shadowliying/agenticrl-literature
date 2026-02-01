# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

import os
# 导入os模块，用于文件和目录路径操作
# 主要用于检查本地分词器文件是否存在

from transformers import AutoTokenizer
# 从transformers库导入AutoTokenizer类
# AutoTokenizer是HuggingFace transformers库的自动分词器
# 能够根据模型名称或路径自动加载对应的分词器

from .base_tokenizer import BaseTokenizer
# 从同级目录导入BaseTokenizer抽象基类
# 使用相对导入确保模块间依赖关系正确

from config import RESOURCES_PATH
# 从config模块导入RESOURCES_PATH配置常量
# RESOURCES_PATH指向本地资源文件夹，用于存储下载的模型和分词器

class TransformersTokenizer(BaseTokenizer):
    # 定义TransformersTokenizer类，继承自BaseTokenizer抽象基类
    # 实现基于HuggingFace transformers库的分词功能
    # 支持本地和远程模型的分词器加载
    
    def __init__(self, tokenizer_name_or_path):
        # 构造函数，初始化transformers分词器
        # 参数tokenizer_name_or_path: 分词器名称或本地路径
        # 可以是HuggingFace模型Hub上的模型名称，也可以是本地路径
        
        _path = os.path.join(RESOURCES_PATH, tokenizer_name_or_path)
        # 构造本地分词器文件的完整路径
        # os.path.join()用于跨平台的路径拼接
        # 将资源目录路径与分词器名称组合成完整的本地路径
        
        if os.path.exists(_path):
            # 检查本地路径是否存在
            # os.path.exists()判断指定路径的文件或目录是否存在
            # 优先使用本地缓存的分词器，避免重复下载
            
            self.tokenizer = AutoTokenizer.from_pretrained(_path)
            # 从本地路径加载分词器
            # from_pretrained()方法可以从本地目录加载预训练的分词器
            # 这样可以避免网络请求，提高加载速度
            
        else:
            # 如果本地路径不存在，则从远程加载
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name_or_path)
            # 从HuggingFace模型Hub下载并加载分词器
            # tokenizer_name_or_path此时被视为模型名称
            # AutoTokenizer会自动下载模型的分词器文件到本地缓存
    
    def tokenize(self, text):
        # 实现父类的抽象方法tokenize，执行文本分词
        # 参数text: 需要分词的文本字符串
        # 返回值: token ID列表
        
        model_inputs = self.tokenizer([text], return_tensors="pt")
        # 使用分词器处理文本，生成模型输入格式
        # [text]: 将文本包装成列表，因为tokenizer期望批量输入
        # return_tensors="pt": 指定返回PyTorch张量格式
        # model_inputs包含input_ids、attention_mask等字段
        
        tokens = model_inputs["input_ids"].tolist()[0]
        # 提取token ID序列并转换为Python列表
        # model_inputs["input_ids"]: 获取token ID张量
        # .tolist(): 将PyTorch张量转换为Python列表
        # [0]: 获取批量输入中的第一个（也是唯一一个）样本
        
        return tokens
        # 返回token ID列表
        # 每个ID对应分词器词汇表中的一个token