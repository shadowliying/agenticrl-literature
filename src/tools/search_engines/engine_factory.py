# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

from typing import Literal
# 从typing模块导入Literal类型注解
# Literal用于限制参数只能取特定的字面值
# 提供更严格的类型检查和更好的IDE代码提示

from .bing_engine import BingEngine
# 从同级目录导入BingEngine类
# BingEngine实现了通过Bing搜索引擎进行网页搜索的功能

from .wiki_engine import WikiEngine
# 从同级目录导入WikiEngine类
# WikiEngine实现了通过Wikipedia API进行知识库搜索的功能

from .serp_engine import SerpEngine
# 从同级目录导入SerpEngine类
# SerpEngine实现了通过SerpAPI进行Google搜索的功能

class EngineFactory(object):
    # 定义搜索引擎工厂类，继承自object（Python 3中可省略）
    # 工厂模式的实现，负责根据引擎名称创建对应的搜索引擎实例
    # 这种设计模式将对象创建逻辑集中管理，便于扩展和维护

    @staticmethod
    # 静态方法装饰器，表示这个方法不需要访问实例或类的状态
    # 可以通过类名直接调用，无需创建EngineFactory实例
    # 适合工厂方法这种纯功能性的操作
    def construct(engine_name:Literal["wiki", "bing", "customized-search", "serp"]):
        # 工厂方法，根据引擎名称创建对应的搜索引擎实例
        # 参数engine_name: 搜索引擎名称，使用Literal类型限制可选值
        # 只能是"wiki"、"bing"、"customized-search"或"serp"中的一个
        # 返回值: 对应的搜索引擎实例，如果名称无效则返回None
        
        search_engine = None
        # 初始化搜索引擎变量为None
        # 如果传入的引擎名称不被支持，将返回None
        # 调用方需要检查返回值是否为None来处理无效引擎名称的情况
        
        if engine_name == "wiki":
            # 检查引擎名称是否为"wiki"
            # 对应Wikipedia搜索引擎
            search_engine = WikiEngine()
            # 创建WikiEngine实例
            # WikiEngine提供Wikipedia知识库搜索功能，适合学术和知识性查询
            
        elif engine_name == "bing":
            # 检查引擎名称是否为"bing"
            # 对应Bing搜索引擎
            search_engine = BingEngine()
            # 创建BingEngine实例
            # BingEngine提供通用网页搜索功能，通过爬取Bing搜索结果实现
            
        elif engine_name == "serp":
            # 检查引擎名称是否为"serp"
            # 对应SerpAPI Google搜索引擎
            search_engine = SerpEngine()
            # 创建SerpEngine实例
            # SerpEngine通过SerpAPI提供稳定的Google搜索功能
            # 相比直接爬取，API方式更可靠且不容易被封禁
            
        # 注意：这里没有处理"customized-search"的情况
        # 可能是预留给将来扩展的自定义搜索引擎
        # 如果传入"customized-search"，将返回None
        
        return search_engine
        # 返回创建的搜索引擎实例
        # 如果引擎名称无效或未实现，返回None
        # 调用方应该检查返回值并适当处理None的情况