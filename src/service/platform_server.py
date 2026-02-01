# encoding: utf-8
# 这行指定文件的字符编码为UTF-8
# UTF-8是一种Unicode编码方式，能够正确处理中文、英文、特殊符号等
# 如果不指定编码，Python可能无法正确显示中文字符

import base64
# 导入base64模块，这是Python标准库的一部分
# base64编码的作用：
# - 将二进制数据（如图片）转换为文本格式
# - 常用于在网络传输中发送图片数据
# - 例如：图片 → base64字符串 → 网络传输 → 解码回图片

import io
# 导入io模块，用于处理输入输出流
# io.BytesIO的作用：
# - 在内存中创建一个"虚拟文件"
# - 可以像操作真实文件一样操作内存中的数据
# - 常用于处理图像、音频等二进制数据

import json
# 导入json模块，用于处理JSON格式数据
# JSON（JavaScript Object Notation）是一种轻量级数据交换格式
# 作用：
# - 将Python字典转换为JSON字符串（序列化）
# - 将JSON字符串转换为Python字典（反序列化）
# - 在网络传输和数据存储中广泛使用

import streamlit as st
# 导入Streamlit库，并给它起一个简短的别名st
# Streamlit是什么？
# - 一个用于快速构建数据应用的Python框架
# - 可以用Python代码直接创建网页界面
# - 无需学习HTML、CSS、JavaScript
# - 非常适合做机器学习、数据分析的展示界面

st.set_page_config(page_title="DeepLiterature", page_icon="logo/icon-title.png")
# 配置Streamlit页面的基本设置
# 这必须是第一个Streamlit命令，用于设置页面的基础配置
# 
# 参数详细说明：
# - page_title: 设置浏览器标签页的标题
#   当用户打开网页时，浏览器标签页会显示"DeepLiterature"
# - page_icon: 设置浏览器标签页的小图标
#   "logo/icon-title.png"是图标文件的路径
#   这个小图标会显示在浏览器标签页的标题前面

import time
# 导入时间模块，提供时间相关的功能
# 主要用途：
# - time.time()：获取当前时间戳（从1970年1月1日开始的秒数）
# - 用于计算程序执行时间
# - 用于性能分析和调试

from utils.logger import model_logger
# 从utils.logger模块导入model_logger对象
# 这是一个日志记录器，用于记录程序运行过程中的信息
# 日志的作用：
# - 记录程序的运行状态
# - 帮助调试程序错误
# - 分析用户使用情况
# - 监控系统性能

from utils.common_utils import *
# 从utils.common_utils模块导入所有公共函数
# *表示导入该模块中所有不以下划线开头的函数和变量
# 注意：这种导入方式虽然方便，但可能导致命名冲突
# common_utils可能包含一些通用的工具函数，如文本处理、格式化等

from queue import Queue
# 从Python标准库导入Queue类
# Queue是什么？
# - 队列数据结构，遵循FIFO（先进先出）原则
# - 线程安全的，多个线程可以同时访问而不会出错
# - 用于在不同线程之间安全地传递数据
# 
# 生活中的例子：
# 队列就像银行排队，先来的人先办业务，后来的人在后面等待

import threading
# 导入线程模块，用于创建和管理多线程
# 为什么需要多线程？
# - 让程序能够同时做多件事情
# - 主线程负责界面显示
# - 后台线程负责处理AI任务
# - 避免界面因为耗时任务而"卡住"

from workflow import deepresearch_workflow
# 导入深度研究工作流模块
# 这是DeepLiterature项目的核心模块
# 作用：
# - 执行实际的AI研究任务
# - 处理用户的问题
# - 调用搜索引擎、大语言模型等
# - 生成最终的答案

from utils.message_queue import WrapperQueue
# 导入封装的消息队列类
# WrapperQueue是对标准Queue的封装，提供了更方便的方法
# 作用：
# - 在主线程（界面）和后台线程（AI处理）之间传递消息
# - 让界面能够实时显示AI的处理进度
# - 实现流式更新效果

from config import LANGUAGE
# 从配置模块导入语言设置
# LANGUAGE是一个全局变量，可能的值：
# - "zh": 中文
# - "en": 英文
# 用于决定界面显示的语言和AI回答的语言

 
def page_chat():
    # 定义页面聊天函数，这是整个聊天界面的核心函数
    # 这个函数包含了聊天页面的所有功能：
    # - 显示聊天历史
    # - 处理用户输入
    # - 调用AI进行回答
    # - 显示AI的思考过程
    # - 管理会话状态
    
    start_time = time.time()
    # 记录函数开始执行的时间戳
    # time.time()返回当前时间的浮点数表示（秒数）
    # 这个时间戳将用于计算整个处理过程的耗时
    # 在最后会计算 time.time() - start_time 得到总耗时
    
    @st.cache_data
    def download_as_json(dict_record):
        # 定义一个带缓存的函数，用于将字典转换为JSON格式的下载数据
        # 
        # @st.cache_data装饰器的作用：
        # - 缓存函数的返回结果
        # - 如果输入参数相同，直接返回缓存的结果，不重新计算
        # - 提高性能，避免重复的计算
        # 
        # 函数参数：
        # - dict_record: dict类型 - 需要转换为JSON的字典数据
        #   例如：{"question": "什么是AI？", "answer": "AI是人工智能..."}
        # 
        # 返回值：
        # - str类型 - 格式化的JSON字符串，可以用于文件下载
        
        return json.dumps(dict_record, indent=4, ensure_ascii=False)
        # json.dumps()将Python字典转换为JSON字符串
        # 参数详解：
        # - dict_record: 要转换的字典对象
        # - indent=4: 设置缩进为4个空格，让JSON更易读
        #   如果不设置缩进，JSON会是一行很长的字符串
        # - ensure_ascii=False: 确保中文字符不被转义
        #   如果设置为True，中文会变成\uxxxx的形式
        #   设置为False，中文会正常显示
    
    def show_jsonl_record():
        # 定义显示JSON格式对话记录的函数
        # 这个函数在用户点击"JSON"按钮时被调用
        # 作用是以结构化的方式展示对话数据
        
        st.markdown("当前数据的整体格式如下: ")
        # st.markdown()用于显示Markdown格式的文本
        # Markdown是一种轻量级标记语言，可以格式化文本
        # 这里显示一个简单的说明文字
        
        with st.container(height=600, border=False):
            # 创建一个Streamlit容器组件
            # 容器的作用：将多个元素组合在一起，统一管理
            # 
            # 参数说明：
            # - height=600: 设置容器高度为600像素
            # - border=False: 不显示容器边框
            # 
            # with语句的作用：
            # - 在这个代码块内的所有Streamlit组件都会放在这个容器里
            # - 当代码块结束时，容器自动关闭
            
            with st.empty():
                # 创建一个空的占位符元素
                # st.empty()的特点：
                # - 创建一个可以被替换的空间
                # - 可以在这个空间里放入任何Streamlit组件
                # - 如果需要更新内容，可以完全替换这个空间的内容
                
                st.write("⏳ 载入数据中...")
                # st.write()用于显示各种类型的内容
                # 这里显示一个加载提示，⏳是Unicode表情符号
                
                st.write(st.session_state.new_record)
                # 显示存储在session state中的新记录数据
                # st.session_state是Streamlit的会话状态管理器
                # 它可以在用户的会话期间保存数据
                # new_record包含了当前对话的详细信息
                
        st.download_button(
            ":grey[下载]", 
            key="download_json", 
            icon="🧾", 
            data=download_as_json(st.session_state.new_record), 
            file_name="chat_record.json", 
            use_container_width=True
        )
        # 创建一个下载按钮，让用户可以下载对话记录
        # 
        # 参数详细说明：
        # - ":grey[下载]": 按钮显示的文字，:grey[]是Streamlit的颜色语法
        # - key="download_json": 按钮的唯一标识符，防止重复
        # - icon="🧾": 按钮上显示的图标（文件夹表情）
        # - data=...: 要下载的数据内容，这里调用download_as_json函数
        # - file_name="chat_record.json": 下载文件的默认名称
        # - use_container_width=True: 按钮宽度占满整个容器


    # 以下是会话状态初始化部分
    # session_state的作用：在用户的整个会话期间保存数据
    # 即使用户刷新页面或重新运行代码，这些数据也会保持

    if "online_answer" not in st.session_state:
        # 检查session_state中是否存在"online_answer"键
        # "not in"操作符检查某个键是否不存在于字典中
        # 如果不存在，说明这是第一次运行或者状态被重置了
        st.session_state.online_answer = ""
        # 初始化在线答案为空字符串
        # 这个变量将存储AI生成的最终答案

    if "online_code_results" not in st.session_state:
        # 检查是否存在代码执行结果的存储空间
        st.session_state.online_code_results = []
        # 初始化为空列表
        # 这个列表将存储AI执行代码产生的结果，如图表、计算结果等

    if "online_answer_stars" not in st.session_state:
        # 检查是否存在答案评分的存储空间
        st.session_state.online_answer_stars = None
        # 初始化为None（空值）
        # 这个变量可能用于存储用户对答案的评分，目前可能还未实现

    if "new_record" not in st.session_state:
        # 检查是否存在新记录的存储空间
        st.session_state.new_record = None
        # 初始化为None
        # 这个变量存储当前对话的完整记录，用于JSON下载功能

    if "show_jsonl" not in st.session_state:
        # 检查是否存在JSON显示标志
        st.session_state.show_jsonl = False
        # 初始化为False
        # 这个布尔值控制是否显示JSON格式的对话记录
        
    st.image("logo/icon.png")
    # 显示应用程序的Logo图片
    # st.image()用于在网页上显示图像
    # "logo/icon.png"是图片文件的相对路径
    
    st.divider()
    # 显示一条水平分隔线
    # st.divider()创建一条细线，用于分隔不同的界面区域
    # 让界面看起来更加整洁和有层次
    
    for msg in st.session_state.messages:
        # 遍历存储在session state中的所有消息
        # st.session_state.messages是一个列表，包含所有的对话消息
        # 每个msg是一个字典，包含角色、内容、头像等信息
        # 例如：{"role": "user", "content": "你好", "avatar": "user.svg"}
        
        with st.chat_message(name=msg["role"], avatar=msg["avatar"]):
            # 创建一个聊天消息容器
            # st.chat_message()是Streamlit专门用于显示聊天消息的组件
            # 
            # 参数说明：
            # - name=msg["role"]: 消息发送者的角色
            #   通常是"user"（用户）或"assistant"（助手）
            # - avatar=msg["avatar"]: 显示的头像图片路径
            #   用户和AI助手会有不同的头像
            
            # 将中间过程还原
            if "step_record" in msg:
                # 检查消息中是否包含步骤记录
                # step_record包含AI思考和处理的详细步骤
                # 只有AI的回复消息才会有这个字段
                
                with st.status("思考过程结束", state="complete", expanded=False):
                    # 创建一个状态展示组件
                    # st.status()用于显示一个可展开/折叠的状态区域
                    # 
                    # 参数说明：
                    # - "思考过程结束": 状态栏显示的标题文字
                    # - state="complete": 状态类型，"complete"表示已完成
                    #   其他可能的值："running"（运行中）、"error"（错误）
                    # - expanded=False: 默认是否展开，False表示默认折叠
                    
                    for now_record in msg['step_record']:
                        # 遍历步骤记录中的每一项
                        # 每个now_record可能是字符串、列表或字典
                        # 不同类型的记录需要用不同方式显示
                        
                        if isinstance(now_record, str):
                            # isinstance()检查对象的类型
                            # 如果now_record是字符串类型
                            st.markdown(now_record, unsafe_allow_html=True) 
                            # 将字符串作为Markdown格式显示
                            # unsafe_allow_html=True允许字符串中包含HTML标签
                            # 这样可以显示更丰富的格式，如颜色、链接等
                            
                        elif isinstance(now_record, list):
                            # 如果记录是列表类型
                            # 通常用于显示检索到的网页链接或文本片段
                            with st.container(height=200):   
                                # 创建一个高度为200像素的容器
                                # 避免列表内容过长影响页面布局
                                st.markdown("\n".join(now_record))
                                # 将列表中的所有项目用换行符连接
                                # "\n".join()将列表转换为多行字符串
                                # 例如：["第一行", "第二行"] → "第一行\n第二行"
                                
                        elif isinstance(now_record, dict):
                            # 如果记录是字典类型
                            # 字典通常包含结构化的数据，如代码和图片
                            
                            if "text" in now_record:
                                # 检查字典中是否有"text"键
                                # "text"通常包含代码或格式化文本
                                st.code(now_record['text'])
                                # st.code()以代码块的形式显示文本
                                # 会自动添加语法高亮和等宽字体
                                
                            if "img" in now_record:
                                # 检查字典中是否有"img"键
                                # "img"包含base64编码的图片数据
                                st.image(io.BytesIO(base64.b64decode(now_record['img'])))   
                                # 显示图片的过程：
                                # 1. base64.b64decode()：将base64字符串解码为字节数据
                                # 2. io.BytesIO()：将字节数据包装成文件流对象
                                # 3. st.image()：显示图片
                                
            if "code_record" in msg:
                # 检查消息中是否包含代码执行记录
                # code_record包含AI执行的代码和产生的结果
                
                for code_results in msg['code_record']:
                    # 遍历代码结果列表
                    # code_results是一个列表，包含多个代码执行结果
                    
                    for code_result in code_results:
                        # 遍历每个具体的代码执行结果
                        # 每个code_result是一个字典，可能包含文本或图片
                        
                        if "text" in code_result:
                            # 如果结果包含文本内容（如代码、输出结果）
                            st.code(code_result['text'])
                            # 以代码块格式显示
                            
                        if "img" in code_result:
                            # 如果结果包含图片内容（如生成的图表）
                            st.image(io.BytesIO(base64.b64decode(code_result['img'])))
                            # 解码并显示base64格式的图片
                            
            st.write(msg["content"])
            # 显示消息的主要内容
            # 这是消息的核心部分，包含用户的问题或AI的回答

    if prompt := st.chat_input("输入文本"):
        # 这是Python的海象操作符（walrus operator）:=
        # 它同时完成两个操作：
        # 1. 创建一个聊天输入框，提示文字是"输入文本"
        # 2. 如果用户输入了内容并按回车，将内容赋值给prompt变量
        # 
        # 等价于：
        # prompt = st.chat_input("输入文本")
        # if prompt:
        #     # 执行后续代码
        
        with st.chat_message(name="user", avatar="logo/user.svg"):
            # 创建用户消息容器
            # name="user"表示这是用户发送的消息
            # avatar指定用户的头像图片
            st.write(prompt)
            # 立即显示用户输入的内容
            
        # 大模型进行回复
        with st.chat_message(name="assistant", avatar="logo/icon-mini.gif"):
            # 创建AI助手消息容器
            # name="assistant"表示这是AI发送的消息
            # avatar使用一个GIF动画作为AI的头像，让界面更生动
            
            # 每次运行前需要清空上一次的结果
            # 这些变量存储的是当前对话轮次的数据
            st.session_state.online_url_lists = []
            # 清空上一次搜索的URL列表
            
            st.session_state.online_steps = []
            # 清空上一次的处理步骤记录
            
            st.session_state.online_answer = ""
            # 清空上一次的答案内容
            
            st.session_state.online_code_results = []
            # 清空上一次的代码执行结果
            
            st.session_state.online_answer_stars = None
            # 清空上一次的答案评分

            # 创建处理上下文
            # context是一个字典，包含处理过程中需要的所有数据
            context = dict()
            # dict()创建一个空字典，等价于{}
            
            context["question"] = prompt
            # 将用户的问题存储到上下文中
            
            context["online_url_lists"] = []
            # 初始化URL列表，用于存储搜索过程中访问的网页
            
            context["online_steps"] = []
            # 初始化步骤列表，用于记录AI的思考和处理过程
            
            context["online_answer"] = ""
            # 初始化答案字符串，用于存储最终生成的回答
            
            context["online_code_results"] = []
            # 初始化代码结果列表，用于存储代码执行的结果
            
            context["online_answer_stars"] = None
            # 初始化评分，目前可能未使用
            

            # 创建线程通信机制
            queue = Queue()
            # 创建一个标准的线程安全队列
            # Queue()是FIFO（先进先出）队列，线程安全
            # 用于在主线程（界面）和工作线程（AI处理）之间传递消息
            
            wrapper_queue = WrapperQueue(queue)
            # 将标准队列包装成WrapperQueue
            # WrapperQueue提供了更方便的方法来处理不同类型的消息
            
            thread = threading.Thread(
                target=deepresearch_workflow.run, 
                args=(prompt, wrapper_queue, WrapperQueue(), LANGUAGE), 
                kwargs={"context": context}
            )
            # 创建一个新的线程来执行AI处理任务
            # 
            # threading.Thread()的参数说明：
            # - target: 线程要执行的函数，这里是deepresearch_workflow.run
            # - args: 传递给target函数的位置参数，是一个元组
            #   * prompt: 用户的问题
            #   * wrapper_queue: 用于向界面发送更新消息的队列
            #   * WrapperQueue(): 一个新的空队列（可能用于其他用途）
            #   * LANGUAGE: 语言设置
            # - kwargs: 传递给target函数的关键字参数，是一个字典
            #   * context: 包含所有处理数据的上下文字典
            
            thread.start()
            # 启动线程，开始执行AI处理任务
            # 注意：start()调用后立即返回，不会等待线程完成
            # 这样主线程可以继续更新界面
            
            with st.status("智能体思考中...", expanded=True, state="running") as status:
                # 创建一个状态显示组件，显示AI正在工作
                # 
                # 参数说明：
                # - "智能体思考中...": 显示的状态文字
                # - expanded=True: 默认展开状态，让用户看到详细过程
                # - state="running": 状态类型为"运行中"，会显示加载动画
                # - as status: 将状态对象赋值给status变量，稍后可以更新它
                
                placeholder = None
                # 初始化占位符变量为None
                # 占位符用于在界面上创建可以动态更新的区域
                
                container = None
                # 初始化容器变量为None
                # 容器用于组织和管理界面元素
                
                while True:
                    # 无限循环，持续处理来自AI处理线程的消息
                    # 这个循环会一直运行，直到收到"finish"或"exception"消息
                    
                    event, message = wrapper_queue.get()
                    # 从队列中获取一条消息
                    # wrapper_queue.get()会阻塞等待，直到有新消息
                    # 返回两个值：事件类型和消息内容
                    
                    # 以下是根据不同事件类型进行不同处理的条件判断
                    if event == "bar":
                        # 如果事件类型是"bar"（进度条文本）
                        st.write_stream(yield_text(message))
                        # st.write_stream()用于流式显示文本
                        # yield_text()可能是一个生成器函数，逐字符显示文本
                        # 创造打字机效果，让文字一个个出现
                        
                    elif event == "placeholder_begin":
                        # 如果事件类型是"开始占位符"
                        placeholder = st.empty()
                        # 创建一个新的空占位符
                        # 这个占位符可以被后续的内容替换
                        
                    elif event == "placeholder_think_stream_markdown":
                        # 如果事件类型是"占位符思考流Markdown"
                        placeholder.markdown(message, unsafe_allow_html=True)
                        # 在占位符中显示Markdown格式的思考内容
                        # 这通常是AI的思考过程，实时更新
                        
                    elif event == "placeholder_caption":
                        # 如果事件类型是"占位符标题"
                        placeholder.caption(message)
                        # 在占位符中显示标题文字
                        # caption()显示较小的、灰色的文字
                        
                    elif event == "placeholder_bar":
                        # 如果事件类型是"占位符进度条"
                        placeholder.write_stream(yield_text(message))
                        # 在占位符中流式显示文本
                        
                    elif event == "placeholder_answer_plain_text":
                        # 如果事件类型是"占位符纯文本答案"
                        placeholder.text(message)
                        # 在占位符中显示纯文本
                        # text()显示没有格式的普通文本
                        
                    elif event == "placeholder_answer_markdown":
                        # 如果事件类型是"占位符Markdown答案"
                        placeholder.markdown(message)
                        # 在占位符中显示Markdown格式的文本
                        
                    elif event == "error":
                        # 如果事件类型是"错误"
                        st.error(message, icon="🔥")
                        # 显示错误消息
                        # st.error()会以红色背景显示错误信息
                        # icon="🔥"显示火焰图标，表示出现了问题
                        
                    elif event == "divider":
                        # 如果事件类型是"分隔线"
                        st.divider()
                        # 显示一条水平分隔线
                        
                    elif event == "container_begin":
                        # 如果事件类型是"开始容器"
                        container = st.container(**message)
                        # 创建一个新容器
                        # **message将message字典中的键值对作为参数传递
                        # 例如：message={"height": 200} → st.container(height=200)
                        
                    elif event == "container_bar":
                        # 如果事件类型是"容器进度条"
                        container.write_stream(yield_text(message))
                        # 在容器中流式显示文本
                        
                    elif event == "container_content":
                        # 如果事件类型是"容器内容"
                        container.markdown(message, unsafe_allow_html=True)
                        # 在容器中显示Markdown内容
                        
                    elif event == "code_result_text":
                        # 如果事件类型是"代码结果文本"
                        st.markdown(message)
                        # 直接在页面上显示代码结果文本
                        
                    elif event == "code_result_image":
                        # 如果事件类型是"代码结果图片"
                        st.image(io.BytesIO(base64.b64decode(message)))
                        # 解码并显示base64格式的图片
                        # 这通常是AI生成的图表或可视化结果
                        
                    elif event == "finish":
                        # 如果事件类型是"完成"
                        break
                        # 跳出while循环，停止处理消息
                        # 表示AI已经完成了所有处理
                        
                    elif event == "exception":
                        # 如果事件类型是"异常"
                        break
                        # 跳出循环，表示处理过程中出现了错误
                        
                status.update(
                    label="思考过程结束", 
                    state="complete", 
                    expanded=False
                )
                # 更新状态组件
                # 
                # 参数说明：
                # - label="思考过程结束": 更新显示的文字
                # - state="complete": 将状态改为"已完成"
                # - expanded=False: 将状态区域折叠起来，节省空间
                
            thread.join()
            # 等待后台线程完成
            # join()会阻塞当前线程，直到被等待的线程执行完毕
            # 确保AI处理完全结束后再继续后续操作

            # 将大模型执行过程中的信息写入session state
            # 这些信息需要保存到会话状态中，以便在页面刷新时保持
            st.session_state.online_url_lists = context["online_url_lists"]
            # 保存搜索过程中访问的URL列表
            
            st.session_state.online_steps = context["online_steps"]
            # 保存AI的处理步骤记录
            
            st.session_state.online_answer = context["online_answer"]
            # 保存AI生成的最终答案
            
            st.session_state.online_code_results = context["online_code_results"]
            # 保存代码执行的结果
            
            st.session_state.online_answer_stars = context["online_answer_stars"]
            # 保存答案评分（如果有的话）
            
            st.session_state.new_record = context.get("new_record")
            # 保存完整的对话记录
            # context.get()是安全的获取方法，如果键不存在返回None
            
            st.session_state.online_answer = re.sub(r'◥\[.*?\]◤', '', st.session_state.online_answer)
            # 使用正则表达式清理答案中的引用标记
            # re.sub()用于替换字符串中匹配的部分
            # 
            # 正则表达式解释：
            # - r'◥\[.*?\]◤': 匹配◥[任意内容]◤格式的文本
            # - ◥和◤是特殊的Unicode字符，用作引用标记
            # - \[和\]：匹配字面的方括号（需要转义）
            # - .*?：匹配任意字符，?表示非贪婪匹配
            # - '': 替换为空字符串，即删除这些标记
            
            st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "logo/user.svg"})
            # 将用户的消息添加到消息历史中
            # append()在列表末尾添加一个新元素
            # 消息格式包含角色、内容和头像信息
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": st.session_state.online_answer, 
                "avatar": "icon-mini.gif", 
                "step_record": st.session_state.online_steps, 
                "code_record": st.session_state.online_code_results
            })
            # 将AI的回复添加到消息历史中
            # AI的消息包含更多信息：
            # - role: 角色为"assistant"
            # - content: 最终的答案内容
            # - avatar: AI的头像
            # - step_record: 思考过程的详细记录
            # - code_record: 代码执行的结果
            
            if len(st.session_state.online_answer) > 0:
                # 检查是否有生成的答案内容
                # len()获取字符串长度，> 0表示不为空
                
                if len(st.session_state.online_code_results) > 0:
                    # 如果有代码执行结果
                    
                    for code_results in st.session_state.online_code_results:
                        # 遍历所有代码结果
                        
                        for code_result in code_results:
                            # 遍历每个具体的代码结果
                            
                            if "text" in code_result:
                                # 如果结果包含文本（如代码、输出）
                                st.code(code_result['text'])
                                # 以代码块格式显示
                                
                            if "img" in code_result:
                                # 如果结果包含图片（如图表）
                                st.image(io.BytesIO(base64.b64decode(code_result['img'])))
                                # 解码并显示图片
                                
                st.write_stream(yield_text(st.session_state.online_answer))
                # 以流式方式显示最终答案
                # 创造打字机效果，让答案逐字出现
            else:
                # 如果没有生成答案内容
                st.error("当前发生了一些错误，请稍后重试...", icon="😵")
                # 显示错误提示信息
                # 😵表情表示出现了问题

      
    if len(st.session_state.online_answer) > 0 and st.session_state.online_answer_stars is None:
        # 检查是否需要显示额外功能
        # 条件：有答案内容 AND 还没有评分
        
        col1, col2, col3 = st.columns([4, 5, 1], vertical_alignment="center")
        # 创建三列布局
        # st.columns()将页面水平分为多列
        # 
        # 参数说明：
        # - [4, 5, 1]: 列的宽度比例，总共10份，分别占4:5:1
        # - vertical_alignment="center": 垂直对齐方式为居中
        
        now_show_jsonl = col1.toggle(
            "🧾 `JSON`", 
            key="jsonl_show", 
            disabled=False if st.session_state.new_record is not None else True, 
            value=st.session_state.show_jsonl
        )
        # 在第一列创建一个切换开关
        # 
        # col1.toggle()的参数说明：
        # - "🧾 `JSON`": 开关的标签文字，🧾是文件图标
        # - key="jsonl_show": 开关的唯一标识符
        # - disabled=...: 是否禁用开关
        #   如果new_record不为None，则disabled=False（启用）
        #   如果new_record为None，则disabled=True（禁用）
        # - value=...: 开关的初始状态
        
        if now_show_jsonl:
            # 如果用户开启了JSON显示开关
            show_jsonl_record()
            # 调用显示JSON记录的函数
            st.rerun()
            # 重新运行整个应用
            # st.rerun()会刷新页面，确保状态更新正确显示
            
    if prompt:
        # 如果用户输入了内容（prompt不为空）
        in_out = {
            "state": "all", 
            "input": {"question": prompt}, 
            "output": "", 
            "response": "", 
            "user_prompt": "", 
            "cost_time": str(round(time.time() - start_time, 3))
        }
        # 创建日志记录字典
        # 
        # 字典包含：
        # - state: 状态标识为"all"
        # - input: 输入信息，包含用户的问题
        # - output: 输出信息（这里为空）
        # - response: 响应信息（这里为空）
        # - user_prompt: 用户提示（这里为空）
        # - cost_time: 计算总耗时
        #   * time.time() - start_time: 当前时间减去开始时间
        #   * round(..., 3): 四舍五入保留3位小数
        #   * str(): 转换为字符串格式
        
        model_logger.info(json.dumps(in_out, ensure_ascii=False))
        # 记录日志信息
        # 
        # 详细过程：
        # 1. json.dumps()将字典转换为JSON字符串
        # 2. ensure_ascii=False确保中文正确显示
        # 3. model_logger.info()以INFO级别记录日志
        # 4. 日志会被写入日志文件，用于调试和分析



# 以下是全局初始化代码，在应用启动时执行

init_message = ""
# 初始化欢迎消息变量为空字符串

if LANGUAGE == "zh":
    # 如果系统语言设置为中文
    init_message = "你好，有什么需要帮忙的？"
    # 设置中文欢迎消息
    
elif LANGUAGE == "en":
    # 如果系统语言设置为英文
    init_message = "Hello, what can I do for you?"
    # 设置英文欢迎消息
    
# 初始化Streamlit会话状态
# 这些状态会在用户的整个会话期间保持

if "never_ask_again" not in st.session_state:
    # 检查是否存在"不再询问"标志
    # 这个标志可能用于某些确认对话框
    st.session_state.never_ask_again = False
    # 初始化为False，表示需要询问用户
    
if "messages" not in st.session_state:
    # 检查是否存在消息历史
    # messages是存储所有对话消息的列表
    st.session_state["messages"] = [
        {
            "role": "assistant", 
            "content": init_message, 
            "avatar": "logo/icon-mini.gif"
        }
    ]
    # 初始化消息列表，包含一条欢迎消息
    # 
    # 消息结构：
    # - role: "assistant"表示这是AI发送的消息
    # - content: 消息内容，使用之前设置的欢迎消息
    # - avatar: AI的头像图片路径



def main():
    # 定义主函数，这是程序的入口点
    # 主函数的作用是组织程序的整体结构
    page_chat()
    # 调用聊天页面函数，启动聊天界面


if __name__ == "__main__":
    # 这是Python的标准模式，检查脚本是否被直接运行
    # 
    # __name__是Python的特殊变量：
    # - 如果脚本被直接运行：__name__ == "__main__"
    # - 如果脚本被其他模块导入：__name__ == "module_name"
    # 
    # 这个条件确保只有在直接运行脚本时才执行main()
    main()
    # 执行主函数，启动整个应用
