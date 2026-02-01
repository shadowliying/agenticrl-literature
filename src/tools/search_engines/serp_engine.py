# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

import requests
# 导入requests库，用于发送HTTP请求到SerpAPI服务
# SerpAPI是第三方Google搜索API服务，提供稳定的搜索接口

from config import SERPAPI_KEY, SERPAPI_URL, SERPAPI_GL, SERPAPI_HL
# 从config模块导入SerpAPI相关的配置常量
# SERPAPI_KEY: SerpAPI的认证密钥，用于身份验证
# SERPAPI_URL: SerpAPI的服务端点URL
# SERPAPI_GL: 地理位置参数，影响搜索结果的地域性
# SERPAPI_HL: 界面语言参数，影响搜索结果的语言

from .base_engine import BaseEngine
# 从同级目录导入BaseEngine抽象基类
# 使用相对导入确保模块间依赖关系正确

class SerpEngine(BaseEngine):
    # 定义SerpEngine类，继承自BaseEngine抽象基类
    # 实现通过SerpAPI进行Google搜索的具体功能
    # SerpAPI提供比直接爬取Google更稳定和合法的搜索接口

    def clean_text(self, input_text):
        # 实现父类的抽象方法clean_text，用于文本清理
        # 参数input_text: 需要清理的输入文本
        return input_text
        # SerpAPI返回的数据已经是结构化的JSON格式
        # 不需要额外的HTML清理，直接返回原文本
        # 这与需要解析HTML的Bing和Wikipedia搜索引擎不同

    def search_title_snippet(self, query, *args, gl=SERPAPI_GL, hl=SERPAPI_HL, **kwargs):
        # 实现父类的抽象方法search_title_snippet，执行Google搜索
        # 参数query: 搜索查询字符串
        # *args: 可变位置参数，用于接收额外的位置参数
        # gl: 地理位置参数，默认使用配置文件中的SERPAPI_GL
        # hl: 语言参数，默认使用配置文件中的SERPAPI_HL
        # **kwargs: 可变关键字参数，用于接收额外的关键字参数（如verbose等）
        
        """
{
    "position": 1,
    "title": "Coffee - Wikipedia",
    "link": "https://en.wikipedia.org/wiki/Coffee",
    "displayed_link": "https://en.wikipedia.org › wiki › Coffee",
    "snippet": "Coffee is a brewed drink prepared from roasted coffee beans, the seeds of berries from certain Coffea species. From the coffee fruit, the seeds are ...",
    "sitelinks": {
        "inline": [
            {
                "title": "History",
                "link": "https://en.wikipedia.org/wiki/History_of_coffee"
            },
            {
                "title": "Coffee bean",
                "link": "https://en.wikipedia.org/wiki/Coffee_bean"
            },
            {
                "title": "Coffee preparation",
                "link": "https://en.wikipedia.org/wiki/Coffee_preparation"
            },
            {
                "title": "Coffee production",
                "link": "https://en.wikipedia.org/wiki/Coffee_production"
            }
        ]
    },
    "rich_snippet": {
        "bottom": {
            "extensions": [
                "Region of origin: Horn of Africa and ‎South Ara...‎",
                "Color: Black, dark brown, light brown, beige",
                "Introduced: 15th century"
            ],
            "detected_extensions": {
                "introduced_th_century": 15
            }
        }
    },
    "about_this_result": {
        "source": {
            "description": "Wikipedia is a free content, multilingual online encyclopedia written and maintained by a community of volunteers through a model of open collaboration, using a wiki-based editing system. Individual contributors, also called editors, are known as Wikipedians.",
            "source_info_link": "https://en.wikipedia.org/wiki/Wikipedia",
            "security": "secure",
            "icon": "https://serpapi.com/searches/6165916694c6c7025deef5ab/images/ed8bda76b255c4dc4634911fb134de53068293b1c92f91967eef45285098b61516f2cf8b6f353fb18774013a1039b1fb.png"
        },
        "keywords": [
            "coffee"
        ],
        "languages": [
            "English"
        ],
        "regions": [
            "the United States"
        ]
    },
    "cached_page_link": "https://webcache.googleusercontent.com/search?q=cache:U6oJMnF-eeUJ:https://en.wikipedia.org/wiki/Coffee+&cd=4&hl=en&ct=clnk&gl=us",
    "related_pages_link": "https://www.google.com/search?q=related:https://en.wikipedia.org/wiki/Coffee+Coffee"
}
"""
        # 多行字符串文档注释，展示SerpAPI返回的JSON数据结构示例
        # 包含了一个完整的搜索结果项的所有字段：
        # - position: 搜索结果在页面中的位置（排名）
        # - title: 搜索结果的标题
        # - link: 搜索结果的URL链接
        # - displayed_link: 在搜索页面显示的链接格式
        # - snippet: 搜索结果的摘要文本
        # - sitelinks: 相关子页面链接（如果有）
        # - rich_snippet: 富文本摘要，包含结构化信息
        # - about_this_result: 关于结果来源的元信息
        # - cached_page_link: Google缓存页面链接
        # - related_pages_link: 相关页面搜索链接
        
        empty_search = False
        # 初始化搜索状态标志为False，表示默认假设搜索会有结果
        # 这个标志用于指示搜索是否返回了有效结果
        
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "gl": gl,
            "hl": hl
        }
        # 构造SerpAPI请求参数字典
        # q: 搜索查询字符串，即用户输入的关键词
        # api_key: SerpAPI的认证密钥，用于身份验证和计费
        # engine: 指定搜索引擎为"google"，SerpAPI支持多种搜索引擎
        # gl: 地理位置参数，影响搜索结果的地域相关性（如"us"、"cn"等）
        # hl: 界面语言参数，影响搜索结果的语言（如"en"、"zh"等）
        
        search_response = requests.get(SERPAPI_URL, params=params)
        # 发送GET请求到SerpAPI服务
        # SERPAPI_URL: 配置文件中定义的SerpAPI端点URL
        # params: 上面构造的请求参数，requests会自动转换为URL查询字符串
        # 返回Response对象，包含API响应的所有信息
        
        if search_response.status_code != 200:
            # 检查HTTP响应状态码是否为200（成功）
            # SerpAPI在正常情况下应该返回200，即使搜索无结果
            empty_search = True
            # 如果请求失败，将搜索状态标志设为True，表示搜索失败
            return empty_search, f"搜索请求失败，状态码: {search_response.status_code}"
            # 返回失败状态和错误信息的元组
            # 第一个元素是布尔值（失败状态），第二个元素是错误描述
        
        search_results = search_response.json().get("organic_results", [])
        # 解析JSON响应并提取有机搜索结果
        # search_response.json(): 将响应的JSON字符串解析为Python字典
        # .get("organic_results", []): 获取"organic_results"字段（有机搜索结果）
        # 如果该字段不存在，返回空列表作为默认值
        # 有机搜索结果是自然排名的搜索结果，不包括广告
        
        for idx in range(len(search_results)):
            # 遍历搜索结果列表，idx为当前索引
            # 使用range(len())而不是enumerate()，因为需要按索引修改列表元素
            
            search_results[idx]["url"] = search_results[idx]["link"]
            # 标准化URL字段名称
            # SerpAPI返回的是"link"字段，但为了与其他搜索引擎保持一致
            # 添加"url"字段，其值与"link"字段相同
            # 这样上层代码可以统一使用"url"字段获取链接
            
            if "snippet" not in search_results[idx]:
                # 检查当前搜索结果是否包含"snippet"字段（摘要）
                # 某些搜索结果可能没有摘要文本
                search_results[idx]["snippet"] = search_results[idx]["title"]
                # 如果没有摘要，则使用标题作为摘要内容
                # 确保每个搜索结果都有snippet字段，避免上层代码出错
                
        if len(search_results) == 0:
            # 检查搜索结果列表是否为空
            # 即使请求成功（状态码200），也可能没有找到相关结果
            empty_search = True
            # 如果没有搜索结果，将搜索状态标志设为True
            
        return empty_search, search_results
        # 返回搜索状态和结果的元组
        # empty_search: 布尔值，表示搜索是否失败或无结果
        # search_results: 搜索结果列表，每个元素包含title、url、snippet等字段

    
