# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

import requests
# 导入requests库，用于发送HTTP请求到Bing搜索服务器
# requests是Python中最常用的HTTP客户端库，提供简洁的API

from bs4 import BeautifulSoup
# 导入BeautifulSoup库，用于解析HTML文档
# BeautifulSoup是强大的HTML/XML解析器，能够从复杂的HTML中提取所需信息

import html
# 导入html模块，提供HTML相关的实用函数
# 主要用于HTML字符实体的编码和解码（如&amp; -> &）

from .base_engine import BaseEngine
# 从同级目录导入BaseEngine抽象基类
# 使用相对导入确保模块依赖关系正确

class BingEngine(BaseEngine):
    # 定义BingEngine类，继承自BaseEngine抽象基类
    # 实现通过Bing搜索引擎进行网页搜索的具体功能

    def clean_text(self, input_text):
        # 实现父类的抽象方法clean_text，用于清理HTML文本
        # 参数input_text: 包含HTML标签和实体的原始文本
        
        # 创建 BeautifulSoup 对象
        soup = BeautifulSoup(input_text, 'html.parser')
        # 使用BeautifulSoup解析输入的HTML文本
        # 'html.parser'指定使用Python内置的HTML解析器
        # soup对象提供了便捷的HTML元素查找和文本提取方法

        # 获取纯净的文本
        clean_text = html.unescape(soup.get_text())
        # soup.get_text(): 提取所有HTML标签内的文本内容，去除HTML标签
        # html.unescape(): 将HTML实体转换为普通字符（如&lt; -> <, &amp; -> &）
        # 最终得到不含HTML标签和实体的纯文本
        
        return clean_text
        # 返回清理后的纯文本字符串

    def search_title_snippet(self, query, lang = "zh", num_results = 10):
        # 实现父类的抽象方法search_title_snippet，执行Bing搜索
        # 参数query: 搜索关键词或查询语句
        # 参数lang: 搜索语言，默认为"zh"（中文）
        # 参数num_results: 期望返回的搜索结果数量，默认10条
        
        url = f"https://www.bing.com/search?q={query}&count={num_results}"
        # 构造Bing搜索的URL
        # q参数：搜索查询词
        # count参数：指定返回结果数量
        # 使用f-string格式化字符串，将参数嵌入URL中
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # 设置HTTP请求头，模拟真实浏览器访问
        # User-Agent: 告诉服务器客户端类型，这里模拟Chrome浏览器
        # 避免被Bing识别为爬虫而被封禁或限制访问
        
        search_response = requests.get(url, headers=headers)
        # 发送GET请求到Bing搜索URL
        # 传入自定义的headers以模拟浏览器行为
        # 返回Response对象，包含服务器响应的所有信息
            
        if search_response.status_code != 200:
            # 检查HTTP响应状态码是否为200（成功）
            # 如果不是200，说明请求失败（可能是网络问题、服务器错误等）
            return f"搜索请求失败，状态码: {search_response.status_code}"
            # 返回错误信息字符串，包含具体的HTTP状态码
            # 常见状态码：404(未找到)、403(禁止访问)、500(服务器错误)等
        
        soup = BeautifulSoup(search_response.text, 'html.parser')
        # 使用BeautifulSoup解析Bing搜索结果页面的HTML内容
        # search_response.text: 获取响应的HTML文本内容
        # 'html.parser': 指定使用Python内置的HTML解析器
    
        search_results = []
        # 初始化空列表，用于存储解析出的搜索结果
        
        for item in soup.find_all('li', class_='b_algo'):
            # 遍历所有class为'b_algo'的li元素
            # 'b_algo'是Bing搜索结果项的CSS类名
            # find_all()返回匹配条件的所有元素列表
            
            title = item.find('h2').get_text()
            # 在当前搜索结果项中查找h2标签（标题元素）
            # get_text()提取标签内的文本内容，去除HTML标签
            # Bing搜索结果的标题通常包含在h2标签中
            
            url = item.find('a')['href']
            # 在当前搜索结果项中查找第一个a标签（链接元素）
            # ['href']获取a标签的href属性值，即目标页面的URL
            # 这是搜索结果指向的实际网页地址
            
            snippet = item.find('p').get_text() if item.find('p') else ''
            # 查找p标签获取搜索结果的摘要文本
            # 使用条件表达式：如果找到p标签则提取文本，否则设为空字符串
            # 避免某些搜索结果没有摘要时出现AttributeError
            
            if len(snippet) > 2 and snippet[:2] == "网页":
                # 检查摘要文本是否以"网页"开头（中文Bing搜索的特殊情况）
                # len(snippet) > 2: 确保文本长度足够进行切片操作
                # snippet[:2]: 获取文本的前两个字符
                snippet = snippet[2:]
                # 如果摘要以"网页"开头，则删除这个前缀
                # snippet[2:]: 从第3个字符开始获取剩余文本
                # 这是针对中文Bing搜索结果格式的特殊处理
                
            search_results.append({'title': title, 'url': url, 'snippet': snippet})
            # 将提取的标题、URL和摘要组装成字典
            # 添加到搜索结果列表中
            # 每个字典包含一条完整的搜索结果信息

        return search_results
        # 返回包含所有搜索结果的列表
        # 每个元素都是包含title、url、snippet键的字典

