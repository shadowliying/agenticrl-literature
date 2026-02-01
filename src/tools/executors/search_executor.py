# encoding: utf-8
# 指定源码文件的字符编码为 UTF-8，确保中文及其他多字节字符被正确解析

from tools.search_engines import EngineFactory
# 从工具库的搜索引擎子模块导入 EngineFactory（工厂类）
# EngineFactory 负责根据给定的引擎名称创建对应的搜索引擎实例（如 wiki、bing、serp）

from .base_executor import BaseExecutor
# 从同级目录的 base_executor 模块导入 BaseExecutor 抽象基类
# 所有执行器（Executor）需继承该基类并实现约定的 execute 接口，以保持统一的调用方式

class SearchExecutor(BaseExecutor):
    # 定义搜索执行器类，继承自 BaseExecutor，提供统一的搜索任务执行入口

    def __init__(self, engine_name):
        # 构造函数接收一个参数 engine_name：字符串，指定要使用的搜索引擎类型
        # 典型取值："wiki"、"bing"、"serp"（具体支持见 EngineFactory.construct）
        self.search_engine = EngineFactory.construct(engine_name)
        # 通过工厂方法，根据传入的引擎名称创建具体的搜索引擎实例并保存到成员变量
        # 若传入不受支持的名称，工厂将返回 None；上层应确保传入有效值或在使用前做校验

    def execute(self, keyword, verbose, *args, **kwargs):    
        # 实现抽象方法 execute，执行一次搜索任务
        # 参数说明：
        # - keyword：字符串，搜索的关键词或查询语句
        # - verbose：布尔值或详细级别开关，控制底层搜索引擎是否输出更详细的日志/过程信息
        # - *args, **kwargs：预留的可变参数，便于未来扩展（与 BaseExecutor 接口保持一致）
        empty_search, new_keyword_search_res =  self.search_engine.search_title_snippet(keyword, verbose=verbose)
        # 调用底层具体引擎的 search_title_snippet 方法发起搜索
        # 约定返回：
        # - empty_search：布尔值，指示本次搜索是否未获得有效结果（True 表示无结果或失败）
        # - new_keyword_search_res：列表或错误信息，通常为若干条包含 title/url/snippet 的搜索结果项
        # 这里将 verbose 作为关键字参数向下传递，让具体引擎自行决定如何使用
        return keyword, empty_search, new_keyword_search_res
        # 返回一个三元组：
        # - 原始 keyword：方便上层在拿到结果时保留查询上下文
        # - empty_search：用于快速判断是否需要降级处理、换引擎、或提示用户
        # - new_keyword_search_res：用于展示或进一步抽取信息的原始搜索结果数据