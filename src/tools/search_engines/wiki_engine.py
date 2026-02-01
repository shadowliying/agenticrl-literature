# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

import requests
# 导入requests库，用于发送HTTP请求到Wikipedia API
# requests是Python中最流行的HTTP客户端库，提供简洁易用的接口

from bs4 import BeautifulSoup
# 导入BeautifulSoup库，用于解析HTML文档和清理HTML标签
# 在Wikipedia搜索中主要用于处理搜索结果中的HTML格式文本

import html
# 导入html模块，提供HTML实体编码和解码功能
# 用于处理Wikipedia API返回的HTML实体字符（如&amp;、&lt;等）

from .base_engine import BaseEngine
# 从同级目录导入BaseEngine抽象基类
# 使用相对导入确保模块间依赖关系正确

class WikiEngine(BaseEngine):
    # 定义WikiEngine类，继承自BaseEngine抽象基类
    # 实现通过Wikipedia API进行知识库搜索的具体功能
    # Wikipedia提供丰富的结构化知识内容，适合学术和知识性查询

    def clean_text(self, input_text):
        # 实现父类的抽象方法clean_text，专门用于清理Wikipedia文本
        # 参数input_text: Wikipedia API返回的可能包含HTML标签的文本
        
        # 创建 BeautifulSoup 对象
        soup = BeautifulSoup(input_text, 'html.parser')
        # 使用BeautifulSoup解析输入的HTML文本
        # 'html.parser'指定使用Python内置的HTML解析器
        # soup对象提供了强大的HTML元素操作功能

        # 移除所有 class="searchmatch" 的 span 标签
        for span in soup.find_all('span', class_='searchmatch'):
            # 查找所有class属性为'searchmatch'的span标签
            # 'searchmatch'是Wikipedia搜索结果中高亮匹配关键词的CSS类
            # find_all返回匹配的所有标签元素列表
            span.unwrap()
            # unwrap()方法移除span标签但保留其内部文本内容
            # 这样可以去除高亮标记但保留实际的文本信息
            # 相当于<span class="searchmatch">关键词</span> -> 关键词

        # 获取纯净的文本
        clean_text = html.unescape(soup.get_text())
        # soup.get_text(): 提取所有HTML标签内的文本内容，去除所有HTML标签
        # html.unescape(): 将HTML实体转换为普通字符（如&amp; -> &, &lt; -> <）
        # 最终得到不含HTML标签和实体的纯文本
        
        return clean_text
        # 返回清理后的纯文本字符串

    def search_title_snippet(self, query, lang="en"):
        # 实现父类的抽象方法search_title_snippet，执行Wikipedia搜索
        # 参数query: 搜索查询字符串，支持关键词、短语或问题
        # 参数lang: Wikipedia语言版本，默认为"en"（英文），也可设置为"zh"（中文）等
        
        search_url = f"https://{lang}.wikipedia.org/w/api.php"
        # 构造Wikipedia API的URL
        # {lang}为语言代码，如en.wikipedia.org或zh.wikipedia.org
        # /w/api.php是Wikipedia的API端点，提供程序化访问接口
        
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "utf8": True
        }
        # 构造Wikipedia API搜索请求的参数字典
        # action: "query" - 指定执行查询操作
        # format: "json" - 指定返回格式为JSON，便于程序解析
        # list: "search" - 指定查询类型为搜索
        # srsearch: 搜索查询字符串，即用户输入的关键词
        # utf8: True - 启用UTF-8编码支持，确保国际字符正确处理
        
        search_response = requests.get(search_url, params=search_params)
        # 发送GET请求到Wikipedia API
        # requests.get()自动将params字典转换为URL查询字符串
        # 返回Response对象，包含API的响应数据
        
        if search_response.status_code != 200:
            # 检查HTTP响应状态码是否为200（成功）
            # Wikipedia API在网络正常时通常返回200，即使搜索无结果
            return f"搜索请求失败，状态码: {search_response.status_code}"
            # 如果状态码不是200，返回错误信息
            # 可能的原因：网络连接问题、API服务异常、请求参数错误等
        
        search_results = search_response.json().get("query", {}).get("search", [])
        # 解析JSON响应并提取搜索结果
        # search_response.json(): 将响应的JSON字符串解析为Python字典
        # .get("query", {}): 获取"query"字段，如果不存在则返回空字典
        # .get("search", []): 获取"search"字段（搜索结果列表），如果不存在则返回空列表
        # 使用链式get()调用避免KeyError异常
        
        for idx, search_res in enumerate(search_results):
            # 遍历搜索结果列表，idx为索引，search_res为当前搜索结果字典
            # enumerate()同时返回索引和元素，便于后续修改列表中的元素
            
            now_title = search_res['title']
            # 提取当前搜索结果的标题
            # Wikipedia搜索结果中的'title'字段包含页面标题
            
            whole_abstract = self.get_abstract(now_title, lang)
            # 调用自定义方法get_abstract获取该页面的完整摘要
            # 传入页面标题和语言代码
            # 使用Wikipedia API的extracts功能获取页面引言部分作为摘要
            
            search_results[idx]['abstract'] = whole_abstract
            # 将获取的摘要添加到当前搜索结果字典中
            # 使用索引idx直接修改原列表中的字典元素
            # 为每个搜索结果添加详细的摘要信息

        return search_results
        # 返回包含摘要信息的完整搜索结果列表
        # 每个元素都包含title、snippet和新增的abstract字段

    
    def get_abstract(self, title, lang = "en"):
        # 定义获取Wikipedia页面摘要的方法
        # 参数title: Wikipedia页面标题
        # 参数lang: 语言代码，默认为英文
        # 该方法通过Wikipedia API获取指定页面的引言摘要
        
        search_url = f"https://{lang}.wikipedia.org/w/api.php"
        # 构造Wikipedia API的URL，与搜索使用相同的端点
        
        # 获取页面摘要
        extract_params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True
        }
        # 构造获取页面摘要的API参数
        # action: "query" - 执行查询操作
        # format: "json" - 返回JSON格式
        # titles: 指定要获取摘要的页面标题
        # prop: "extracts" - 指定获取页面摘要内容
        # exintro: True - 只获取引言部分（通常是第一段）
        # explaintext: True - 返回纯文本，不包含HTML标签

        extract_response = requests.get(search_url, params=extract_params)
        # 发送GET请求获取页面摘要
        
        if extract_response.status_code != 200:
            # 检查HTTP响应状态码
            return f"摘要请求失败，状态码: {extract_response.status_code}"
            # 如果请求失败，返回错误信息
        
        pages = extract_response.json().get("query", {}).get("pages", {})
        # 解析JSON响应，提取pages字段
        # pages字段包含请求页面的详细信息，以页面ID为键

        page_id = next(iter(pages))
        # 获取pages字典中的第一个（也是唯一一个）页面ID
        # iter(pages)创建迭代器，next()获取第一个键
        # 因为只请求了一个页面，所以pages只包含一个键值对
        
        abstract = pages[page_id].get("extract", "摘要不可用")
        # 从页面信息中提取"extract"字段（摘要内容）
        # 如果extract字段不存在，则返回默认值"摘要不可用"
        
        return html.unescape(abstract)
        # 对摘要文本进行HTML实体解码并返回
        # 确保特殊字符（如&amp;、&lt;等）正确显示