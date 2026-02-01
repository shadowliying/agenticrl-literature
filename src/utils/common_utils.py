# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

import os
# 导入os模块，用于操作系统相关的功能
# 主要用于文件路径操作、目录遍历等系统级操作

import re
# 导入re模块，提供正则表达式功能
# 用于字符串模式匹配、文本清理、特殊格式提取等操作

import time
# 导入time模块，提供时间相关的功能
# 主要用于延迟操作、时间戳处理等

import pandas as pd
# 导入pandas库，提供数据分析和处理功能
# 主要用于DataFrame操作、JSON文件读取和数据合并

import json
# 导入json模块，用于JSON数据的序列化和反序列化
# 支持Python对象与JSON字符串之间的转换

from datetime import datetime
# 从datetime模块导入datetime类
# 用于获取当前时间、时间格式化等日期时间操作

import pytz
# 导入pytz库，提供时区处理功能
# 用于时区转换、获取特定时区的时间等操作

from config import LANGUAGE
# 从config模块导入LANGUAGE配置常量
# 用于根据语言设置返回不同语言的内容

def get_real_time_str():
    # 定义获取实时时间字符串的函数
    # 返回值：格式化的日期时间字符串，北京时间
    # 用于在日志、界面显示等场景提供统一的时间格式
    
    now_utc = datetime.now(pytz.utc)
    # 获取当前UTC时间
    # datetime.now(pytz.utc)创建一个带时区信息的datetime对象
    # UTC是协调世界时，作为时间转换的基准
    
    beijing_tz = pytz.timezone('Asia/Shanghai')
    # 创建北京时区对象
    # 'Asia/Shanghai'是北京时区的标准时区标识符
    # 中国大陆统一使用北京时间（UTC+8）
    
    now_beijing = now_utc.astimezone(beijing_tz)
    # 将UTC时间转换为北京时间
    # astimezone()方法进行时区转换
    # 确保显示的是用户本地的时间
    
    formatted_date = now_beijing.strftime("%Y-%m-%d")
    # 格式化日期部分
    # strftime()方法将datetime对象格式化为字符串
    # "%Y-%m-%d"格式：年-月-日，如"2024-01-15"
    
    formatted_time = now_beijing.strftime("%H:%M:%S")
    # 格式化时间部分
    # "%H:%M:%S"格式：24小时制的时:分:秒，如"14:30:25"
    
    return f"{formatted_date} {formatted_time}"
    # 返回完整的日期时间字符串
    # 使用f-string将日期和时间组合，格式如"2024-01-15 14:30:25"

def get_location_by_ip():
    # 定义根据IP获取位置信息的函数
    # 注意：这个函数实际上是模拟的，没有真正获取IP地址
    # 返回值：格式化的位置字符串
    
    if LANGUAGE == "en":
        # 检查配置的语言是否为英文
        # 根据不同语言返回不同的位置信息
        
        location_response = {
            "city": "Beijing",
            "regionName": "Beijing",
            "country": "China",
        }
        # 创建英文版本的位置信息字典
        # 包含城市、地区和国家的英文名称
        # 这里使用固定的北京位置信息作为示例
        
    else:
        # 如果语言不是英文（假设为中文）
        location_response = {
                "city": "北京",
                "regionName": "北京市",
                "country": "中国",
            }
        # 创建中文版本的位置信息字典
        # 包含城市、地区和国家的中文名称
        
    location_response = json.dumps(location_response)
    # 将位置信息字典序列化为JSON字符串
    # json.dumps()将Python字典转换为JSON格式的字符串
    
    location_data = json.loads(location_response)
    # 将JSON字符串反序列化为Python字典
    # json.loads()将JSON字符串转换回Python对象
    # 这里的序列化和反序列化操作似乎是为了模拟真实的API响应处理
    
    city = location_data.get('city', '未知')
    # 从位置数据中提取城市信息
    # get()方法安全地获取字典值，如果键不存在返回默认值'未知'
    
    region = location_data.get('regionName', '未知')
    # 从位置数据中提取地区信息
    # 同样使用安全的get()方法，避免KeyError异常
    
    country = location_data.get('country', '未知')
    # 从位置数据中提取国家信息
    # 如果数据中没有对应字段，返回'未知'作为默认值

    return f"{city}, {region}, {country}"
    # 返回格式化的位置字符串
    # 使用逗号和空格分隔城市、地区和国家信息
    # 例如："北京, 北京市, 中国"



def escape_ansi(line: str) -> str:
    # 定义清除ANSI转义序列的函数
    # 参数line: 包含ANSI转义序列的字符串
    # 返回值: 清除ANSI转义序列后的纯文本字符串
    # ANSI转义序列用于控制终端文本样式（颜色、粗体、下划线等）
    
    # 删除文本中的 ANSI 转移序列(ANSI 转义序列通常用于控制终端文本的样式，如颜色、粗体、下划线等)
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    # 创建ANSI转义序列的正则表达式模式
    # \x1B: ESC字符（十六进制1B，即ASCII码27）
    # [@-_]: 匹配@到_之间的字符
    # [\x80-\x9F]: 匹配十六进制80-9F范围的控制字符
    # [0-?]*: 匹配0到?之间的字符，零次或多次
    # [ -/]*: 匹配空格到/之间的字符，零次或多次
    # [@-~]: 匹配@到~之间的字符，作为转义序列的结束
    
    return ansi_escape.sub('', line)
    # 使用正则表达式替换所有匹配的ANSI转义序列为空字符串
    # sub()方法执行替换操作，第一个参数是替换内容，第二个参数是目标字符串
    # 返回清理后的纯文本，去除所有终端样式控制字符

def split_process_jsonl(search_process):
    # 定义处理搜索流程的函数
    # 参数search_process: 搜索过程的数据结构，包含多个搜索阶段
    # 返回值: 格式化的处理步骤列表，用于界面显示
    # 这个函数将复杂的搜索过程转换为用户友好的步骤描述
    
    process_list = []
    # 初始化空的处理步骤列表
    # 用于存储格式化后的每个处理步骤
    
    for search_stage in search_process:
        # 遍历搜索过程中的每个阶段
        # search_stage包含该阶段的所有功能调用选项
        
        is_websearch = False
        # 初始化网页搜索标志为False
        # 用于标记当前阶段是否包含网页搜索功能
        
        is_coderunner = False
        # 初始化代码执行标志为False
        # 用于标记当前阶段是否包含代码执行功能
        
        is_mclick = False
        # 初始化多点击标志为False
        # 用于标记当前阶段是否包含网页阅读功能
        
        content = ""
        # 初始化内容字符串为空
        # 用于存储当前阶段的格式化内容
        
        for fc_option in search_stage:
            # 遍历当前搜索阶段的所有功能调用选项
            # fc_option代表一个具体的功能调用（function call）
            
            if fc_option['name'] == "webSearch":
                # 检查是否为网页搜索功能
                is_websearch = True
                # 设置网页搜索标志为True
                
                content += ":grey-background[" + fc_option['keyword'] +"] "
                # 添加搜索关键词到内容字符串
                # :grey-background[]是Streamlit的markdown格式，创建灰色背景
                # fc_option['keyword']包含搜索的关键词
                
            elif fc_option['name'] == "mclick":
                # 检查是否为多点击（网页阅读）功能
                is_mclick = True
                # 设置多点击标志为True
                
                fc_option['keyword'] = [idx + 1 for idx in fc_option['keyword']]
                # 将索引转换为从1开始的编号
                # 原始索引是从0开始，用户界面显示从1开始更直观
                
                for keyword in fc_option['keyword']:
                    # 遍历所有选中的网页索引
                    content += ":blue-background[" + "📃" + str(keyword) +"] "
                    # 为每个选中的网页添加蓝色背景标签
                    # 📃表情符号表示文档，str(keyword)是网页编号
                    
            elif fc_option['name'] == "CodeRunner":
                # 检查是否为代码执行功能
                is_coderunner = True
                # 设置代码执行标志为True
                
                if len(fc_option['keyword']) > 19:
                    # 如果代码内容长度超过19个字符
                    plat_text = fc_option['keyword'][:19].replace("\n", " ").replace("\r", " ")
                    # 截取前19个字符并清理换行符
                    # replace()将换行符替换为空格，保持文本在一行显示
                else:
                    # 如果代码内容长度不超过19个字符
                    plat_text = fc_option['keyword'].replace("\n", " ").replace("\r", " ")
                    # 直接清理换行符，不进行截取
                    
                content += ":grey-background[" + f"🐍 {plat_text}..." +"] "
                # 添加代码片段到内容字符串
                # 🐍表情符号表示Python代码，...表示内容被截取

        if is_websearch:   
            # 如果当前阶段包含网页搜索
            process_list.append("🤖 智能体 · 生成关键词：" + content)
            # 添加关键词生成步骤到处理列表
            # 🤖表示AI智能体操作
            
            process_list.append("🔍 调工具 · 搜索引擎")
            # 添加搜索引擎调用步骤
            # 🔍表示搜索操作

        if is_mclick:
            # 如果当前阶段包含网页阅读
            process_list.append("🤖 智能体 · 选择网页深入阅读：" + content)
            # 添加网页选择步骤到处理列表
            # 显示选中的网页编号
            
            process_list.append("📖 调工具 · 网页阅读")
            # 添加网页阅读步骤
            # 📖表示阅读操作
            # st.write("📖 打开：" + content)
            # 注释掉的代码，可能用于Streamlit界面调试

        if is_coderunner:
            # 如果当前阶段包含代码执行
            process_list.append("🤖 智能体 · 生成代码：" + content)
            # 添加代码生成步骤到处理列表
            # 显示生成的代码片段
            
            process_list.append("🧩 调工具 · 代码执行")
            # 添加代码执行步骤
            # 🧩表示代码执行操作

    return process_list
    # 返回完整的处理步骤列表
    # 每个元素都是格式化的步骤描述，用于界面展示

def find_special_text_and_numbers(text):
    # 定义查找特殊格式文本和数字的函数
    # 参数text: 包含特殊标记的文本字符串
    # 返回值: 包含特殊文本列表和对应数字列表的元组
    # 用于处理文档引用标记，如◥[1,2,3]◤格式
    
    pattern = r'◥\[(\d+(?:[,\，]\s*\d+)*)\]◤'
    # 定义正则表达式模式来匹配特殊引用格式
    # ◥\[: 匹配字面量"◥["
    # (\d+(?:[,\，]\s*\d+)*): 捕获组，匹配一个或多个用逗号分隔的数字
    #   \d+: 匹配一个或多个数字
    #   (?:[,\，]\s*\d+)*: 非捕获组，匹配零个或多个",数字"或"，数字"模式
    #   [,\，]: 匹配英文逗号或中文逗号
    #   \s*: 匹配零个或多个空白字符
    # \]◤: 匹配字面量"]◤"
    
    matches = re.findall(pattern, text)
    # 使用正则表达式查找所有匹配的模式
    # findall()返回所有匹配的捕获组内容（即括号内的数字字符串）

    # 提取文本和数字列表
    special_texts = [f'◥[{nums}]◤' for nums in matches]
    # 重构完整的特殊文本标记
    # 使用列表推导式为每个匹配的数字字符串重新构建完整格式
    
    number_lists = [[int(num) for num in re.split(r'[,\，]', nums)] for nums in matches]
    # 将数字字符串转换为整数列表
    # 外层列表推导式：遍历每个匹配的数字字符串
    # re.split(r'[,\，]', nums): 按英文或中文逗号分割数字字符串
    # 内层列表推导式：将每个数字字符串转换为整数
    
    return special_texts, number_lists
    # 返回特殊文本列表和对应的数字列表
    # special_texts: ['◥[1,2]◤', '◥[3]◤']
    # number_lists: [[1, 2], [3]]

def replace_ref_tag2md(origin_llm_answer, url_list):
    # 定义将引用标记转换为Markdown链接的函数
    # 参数origin_llm_answer: 包含引用标记的原始LLM回答
    # 参数url_list: URL信息列表，包含标题和链接
    # 返回值: 转换后的Markdown格式文本
    # 用于将AI回答中的引用标记转换为可点击的链接
    
    new_llm_answer = origin_llm_answer
    # 创建原始答案的副本
    # 避免修改原始数据，保持数据的不可变性
    
    special_texts, special_numbers = find_special_text_and_numbers(origin_llm_answer)
    # 调用前面定义的函数查找特殊引用标记
    # special_texts: 完整的引用标记文本
    # special_numbers: 对应的数字列表
    
    for special_id, numbers in enumerate(special_numbers):
        # 遍历每个引用标记及其对应的数字列表
        # special_id: 当前引用标记的索引
        # numbers: 当前引用标记包含的数字列表
        
        replace_str = ""
        # 初始化替换字符串为空
        # 用于构建Markdown链接字符串
        
        # 遍历所有引用的标记
        for number in numbers:
            # 遍历当前引用标记中的每个数字
            if number < len(url_list):
                # 检查数字是否在有效范围内
                # 避免数组越界错误
                
                new_title = url_list[number]['title'].replace('"', "'")
                # 获取对应URL的标题并清理双引号
                # 将双引号替换为单引号，避免Markdown语法冲突
                
                replace_str += f" [:blue-background[{number + 1}]]({url_list[number]['url']} \"{new_title}\") "
                # 构建Markdown链接格式
                # [:blue-background[{number + 1}]]: Streamlit样式的蓝色背景文本
                # ({url_list[number]['url']} "{new_title}"): Markdown链接语法
                # number + 1: 将0基索引转换为1基显示
            else:
                # 如果数字超出URL列表范围
                replace_str = ""
                # 将替换字符串重置为空，忽略无效引用
                
        new_llm_answer = new_llm_answer.replace(special_texts[special_id], replace_str)
        # 将特殊引用标记替换为Markdown链接
        # 使用字符串的replace方法进行文本替换

    return new_llm_answer
    # 返回转换后的文本
    # 所有引用标记都被替换为可点击的Markdown链接

def text_finish(idx, text):
    # 定义文本完成状态格式化函数
    # 参数idx: 步骤索引（1-10）
    # 参数text: 步骤描述文本
    # 返回值: 格式化的完成状态文本
    # 用于显示已完成的处理步骤
    
    numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    # 定义数字表情符号列表
    # 用于替代普通数字，提供更好的视觉效果
    # 支持1-10的步骤编号
    
    return "*:grey[" + numbers[idx-1] + " ~~" + text  + "~~]*  [:green[已完成]]"
    # 返回格式化的完成状态文本
    # *:grey[...]*: Streamlit的灰色斜体格式
    # numbers[idx-1]: 获取对应的数字表情符号（idx-1因为数组从0开始）
    # ~~text~~: 删除线格式，表示已完成
    # [:green[已完成]]: 绿色的"已完成"标签

def text_render(idx, text):
    # 定义文本渲染函数
    # 参数idx: 步骤索引（1-10）
    # 参数text: 步骤描述文本
    # 返回值: 格式化的步骤文本
    # 用于显示进行中或待处理的步骤
    
    numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    # 定义数字表情符号列表
    # 与text_finish函数使用相同的数字符号，保持一致性
    
    if "已完成" in text:
        # 检查文本是否已包含"已完成"标记
        return text
        # 如果已经是完成状态，直接返回原文本
        # 避免重复格式化
        
    return numbers[idx-1] + " " + text
    # 返回带数字前缀的步骤文本
    # numbers[idx-1]: 获取对应的数字表情符号
    # " " + text: 添加空格和原始文本

def is_mobile(user_agent):
    # 定义移动设备检测函数
    # 参数user_agent: HTTP请求中的User-Agent字符串
    # 返回值: 布尔值，True表示移动设备，False表示桌面设备
    # 用于根据设备类型调整界面显示
    
    mobile_keywords = [
        'Android', 'iPhone', 'iPad', 'Windows Phone', 'Mobile', 'Symbian',
        'BlackBerry', 'Opera Mini', 'IEMobile', 'UCBrowser', 'MQQBrowser'
    ]
    # 定义移动设备的关键词列表
    # 包含主流移动操作系统和浏览器的标识符
    # Android: 安卓系统
    # iPhone/iPad: 苹果iOS设备
    # Windows Phone: 微软移动系统
    # Mobile: 通用移动设备标识
    # Symbian: 诺基亚系统
    # BlackBerry: 黑莓设备
    # Opera Mini: 轻量级浏览器
    # IEMobile: 微软移动浏览器
    # UCBrowser/MQQBrowser: 中国常用移动浏览器
    
    # 检查User-Agent中是否包含手机端的关键词
    for keyword in mobile_keywords:
        # 遍历所有移动设备关键词
        if keyword.lower() in user_agent.lower():
            # 进行不区分大小写的字符串包含检查
            # lower()方法将字符串转换为小写，确保匹配的准确性
            return True
            # 如果找到任何移动设备关键词，立即返回True
            
    return False
    # 如果没有找到任何移动设备关键词，返回False
    # 表示这是桌面设备或其他非移动设备


def latex_render(text):
    # 定义LaTeX渲染预处理函数
    # 参数text: 包含LaTeX格式的原始文本
    # 返回值: 处理后的文本，适合在Web界面中渲染
    # 用于将LaTeX数学公式转换为Web友好的格式
    
    text = text.replace("\\(","$").replace("\\)","$")  
    # 将LaTeX的行内数学公式标记转换为Markdown格式
    # \\(和\\): LaTeX的行内数学公式标记
    # $和$: Markdown/MathJax的行内数学公式标记
    # 这种转换使数学公式能在Web界面中正确显示
    
    lines = text.splitlines()
    # 将文本按行分割为列表
    # splitlines()方法按换行符分割字符串，返回行的列表
    
    final_text = []
    # 初始化最终文本行列表
    # 用于存储过滤后的文本行
    
    for line in lines:
        # 遍历每一行文本
        if line[:6] == "![fig-":
            # 检查行是否以"![fig-"开头
            # 这是Markdown图片链接的格式，通常用于引用图表
            # 在某些场景下可能不需要显示这些图片引用
            continue
            # 跳过图片引用行，不添加到最终文本中
            
        final_text.append(line)
        # 将非图片引用行添加到最终文本列表
        
    return "\n".join(final_text)
    # 重新组合文本行并返回
    # join()方法使用换行符连接所有文本行

def yield_text(text, speed = 0.02):
    # 定义流式文本输出生成器函数
    # 参数text: 要输出的完整文本
    # 参数speed: 输出速度（秒），默认0.02秒每字符/片段
    # 返回值: 生成器，逐步产出文本片段
    # 用于模拟打字机效果或流式输出
    
    # 模拟流式输出
    i = 0  # 用来跟踪当前处理的字符位置
    # 初始化字符位置索引
    # 用于遍历整个文本字符串
    
    while i < len(text):
        # 循环直到处理完所有字符
        if text[i:i+17] == ":blue-background[" or text[i:i+17] == ":grey-background[":
            # 检查是否遇到特殊格式标记的开始
            # :blue-background[: 蓝色背景格式
            # :grey-background[: 灰色背景格式
            # 这些是Streamlit的特殊标记格式
            
            end_pos = i + 17  # 跳过 ":blue-background["
            # 设置结束位置的初始值
            # 从格式标记后开始查找结束符
            
            while end_pos < len(text) and text[end_pos] not in [']']:
                # 查找格式标记的结束符"]"
                end_pos += 1
                # 逐个字符向前查找
                
            if end_pos < len(text):  # 找到匹配的结束符
                # 确保找到了有效的结束符
                end_pos += 1  # 包含闭合符号
                # 将结束位置移动到结束符之后
                
                yield text[i:end_pos]  # 一次性返回这一部分
                # 产出完整的格式标记文本
                # 避免格式标记被分割导致显示错误
                
                i = end_pos  # 更新 i 跳到下一个位置
                # 更新当前位置到格式标记之后
                
        # 检查是否遇到以 http 开头的字符串
        elif text[i:i+4] == "http":
            # 检查是否遇到URL链接
            # HTTP或HTTPS链接通常以"http"开头
            
            end_pos = i + 4  # 跳过 "http"
            # 设置URL查找的起始位置
            
            while end_pos < len(text) and text[end_pos] not in [")", "\n"]:
                # 查找URL的结束位置
                # ")"表示Markdown链接的结束
                # "\n"表示换行，URL通常不跨行
                end_pos += 1
                # 逐个字符查找URL的结束
                
            yield text[i:end_pos]  # 一次性返回这一段 URL，处理标题中乱码的问题
            # 产出完整的URL
            # 避免URL被分割导致链接失效或显示乱码
            
            i = end_pos  # 更新 i 跳到下一个位置
            # 更新当前位置到URL之后
            
        else:
            # 如果没有特殊格式，逐字符返回
            yield text[i]
            # 产出单个字符
            # 正常的文本逐字符输出，实现打字机效果
            
            i += 1
            # 移动到下一个字符
            
        time.sleep(speed)  # 模拟流式返回的延迟
        # 添加延迟以控制输出速度
        # speed参数控制每个片段的输出间隔

def merge_jsonl(folder_path = "./datasets/web_8_turns"):
    # 定义合并JSONL文件的函数
    # 参数folder_path: 包含JSONL文件的文件夹路径，默认为数据集目录
    # 返回值: 合并后的pandas DataFrame
    # 用于数据预处理，将多个JSONL文件合并为单个数据集
    
    # 初始化一个空的 DataFrame
    all_data = pd.DataFrame()
    # 创建空的pandas DataFrame用于存储合并后的数据
    # DataFrame是pandas的核心数据结构，类似于Excel表格

    # 遍历文件夹下所有的 .jsonl 文件
    for filename in os.listdir(folder_path):
        # 获取指定文件夹下的所有文件名
        # os.listdir()返回目录中所有文件和子目录的名称列表
        
        if filename.endswith('.jsonl'):
            # 检查文件是否为JSONL格式
            # endswith()方法检查字符串是否以指定后缀结尾
            # JSONL是JSON Lines格式，每行是一个JSON对象
            
            file_path = os.path.join(folder_path, filename)
            # 构建完整的文件路径
            # os.path.join()进行跨平台的路径拼接
            
            df = pd.read_json(file_path, lines=True)
            # 读取JSONL文件为DataFrame
            # lines=True参数告诉pandas这是JSONL格式（每行一个JSON对象）
            
            df = df[df['messages'].apply(lambda x: len(x) >= 8)]
            # 过滤数据，只保留messages字段长度>=8的记录
            # apply()方法对每行应用lambda函数
            # lambda x: len(x) >= 8检查messages列表的长度
            # 这可能是为了确保对话轮次足够多
            
            all_data = pd.concat([all_data, df], ignore_index=True)
            # 将当前文件的数据合并到总数据集中
            # pd.concat()函数连接多个DataFrame
            # ignore_index=True重新生成连续的索引

    return all_data
    # 返回合并后的完整数据集
    # 包含所有符合条件的JSONL文件数据
