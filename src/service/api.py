# encoding: utf-8
# 设置文件编码为UTF-8，确保中文内容正确处理

from fastapi import FastAPI, Request
# 导入FastAPI相关组件：
# - FastAPI: 这是核心类，用于创建Web应用实例 写python后端接口的框架
# - Request: 请求对象，包含客户端发送的所有信息（URL、头部、请求体等）

import uvicorn, json
# 导入两个重要模块：
# - uvicorn: 这是一个ASGI服务器，专门用来运行FastAPI应用
#   ASGI = Asynchronous Server Gateway Interface（异步服务器网关接口）
# - json: Python标准库，用于处理JSON数据的序列化（转换为字符串）和反序列化（解析字符串）

from fastapi.responses import StreamingResponse
# 导入StreamingResponse类，这是FastAPI提供的特殊响应类型
# 用于实现"流式响应" - 即数据可以一边生成一边发送给客户端
# 而不需要等待所有数据都准备好再一次性发送

from queue import Queue
# 导入Python标准库中的Queue类
# Queue是一个线程安全的队列，遵循FIFO（先进先出）原则
# 用于在不同线程之间安全地传递数据

import threading
# 导入Python的线程模块
# 线程允许程序同时执行多个任务
# 这里用于创建后台线程来处理耗时的研究任务

import sys,os
# 导入系统相关模块：
# - sys: 提供与Python解释器交互的功能
# - os: 提供与操作系统交互的功能，如文件路径操作

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 这是一个复杂的路径计算，让我们分步解析：
# 1. __file__ 是当前文件（api.py）的路径
# 2. os.path.abspath(__file__) 获取当前文件的绝对路径
# 3. os.path.dirname() 第一次调用：获取父目录（service目录）
# 4. os.path.dirname() 第二次调用：再获取父目录（src目录）
# 最终结果：ROOT_PATH指向项目的src目录

sys.path.append(ROOT_PATH)
# 将src目录添加到Python的模块搜索路径中
# 这样就可以直接导入src目录下的其他模块
# 比如可以写 from utils import xxx 而不需要写 from src.utils import xxx

from utils.message_queue import WrapperQueue
# 导入项目自定义的消息队列包装类
# WrapperQueue是对标准Queue的封装，提供了更方便的接口

from workflow import deepresearch_workflow
# 导入深度研究工作流模块
# 这是整个系统的核心，负责执行实际的研究任务

from config import LANGUAGE
# 导入语言配置
# LANGUAGE变量决定系统使用中文还是英文

def generator(wrapper_queue):
    # 定义一个生成器函数，用于将队列中的消息转换为SSE格式
    # 生成器是Python的特殊函数，使用yield关键字，可以"记住"执行状态
    # 每次调用时从上次yield的地方继续执行
    # 
    # 参数说明：
    # wrapper_queue: WrapperQueue类型，包含要发送给客户端的消息
    # 
    # 什么是SSE（Server-Sent Events）？
    # SSE是一种Web标准，允许服务器主动向客户端推送数据
    # 格式为: "data: 消息内容\n\n"
    
    while True:
        # 无限循环，持续处理队列中的消息
        
        message = wrapper_queue.get()
        # 从队列中获取一条消息
        # 如果队列为空，这个方法会阻塞（暂停执行），直到有新消息到达
        
        if message == "finish":
            # 检查是否收到结束信号
            # "finish"是一个特殊标记，表示所有处理已完成
            
            yield "data: [DONE]\n\n"
            # 使用yield返回SSE格式的结束标记
            # "[DONE]"是OpenAI API的标准结束标记
            # "\n\n"是SSE格式要求的结尾
            
            return
            # 结束生成器函数，停止发送数据
            
        if message == "exception":
            # 检查是否收到异常信号
            # "exception"表示处理过程中发生了错误
            
            yield "data: [ERROR]\n\n"
            # 发送错误标记给客户端
            
            return
            # 结束生成器函数
            
        if type(message) == type(dict()):
            # 检查消息是否为字典类型
            # type(dict())是获取字典类型的一种方式
            # 也可以写成 isinstance(message, dict)
            
            message = json.dumps(message, ensure_ascii=False)
            # 将字典转换为JSON字符串
            # ensure_ascii=False 确保中文字符不会被转义成\uxxxx格式
            
        yield f"data: {message}\n\n"
        # 将消息以SSE格式发送给客户端
        # f"..." 是Python的f-string语法，用于字符串格式化
        # 等价于 "data: " + str(message) + "\n\n"


app = FastAPI()
# 创建FastAPI应用实例
# 这个实例将处理所有的HTTP请求
# FastAPI会自动处理请求路由、参数验证、响应格式化等

@app.post("/stream")
# 这是一个装饰器（decorator），定义了一个API端点
# @app.post 表示这个端点只接受POST请求
# "/stream" 是URL路径，完整URL是 http://服务器地址:端口/stream
# 
# 为什么用POST而不是GET？
# - POST请求可以在请求体中携带复杂数据（如JSON）
# - GET请求只能在URL参数中传递简单数据

async def create_item(request: Request):
    # 定义异步函数来处理/stream端点的请求
    # 
    # async关键字说明：
    # - async表示这是一个异步函数
    # - 异步函数可以在等待某些操作时释放CPU给其他任务
    # - 提高服务器处理并发请求的能力
    # 
    # 参数说明：
    # - request: Request类型，包含客户端发送的所有请求信息
    # - 函数名create_item是随意起的，可以是任何名字
    # 当客户端调用 /stream 时，
    # FastAPI 会把这次 HTTP 请求封装成一个 Request 对象，
    # 然后按函数签名把它传给你的处理函数
    # 
    # 返回值类型暗示：
    # FastAPI会根据return语句自动确定返回类型
    
    json_post_raw = await request.json()
    # 从请求中提取JSON数据
    # await关键字说明：
    # - await只能在async函数中使用
    # - 表示等待一个异步操作完成
    # - request.json()是异步方法，因为读取请求体可能需要时间
    # 
    # 期望的JSON格式：
    # {
    #     "query": "用户的问题"
    # }
    
    query = json_post_raw.get("query")
    # 从JSON数据中提取"query"字段
    # .get()方法是安全的，如果字段不存在会返回None而不会报错
    # 也可以写成 json_post_raw["query"]，但如果字段不存在会抛出异常

    context = dict()
    # 创建一个空字典，用于存储处理过程中的所有数据
    # dict()等价于{}，两种写法都可以创建空字典
    
    context['question'] = query
    # 在上下文中存储用户的问题
    
    context["online_url_lists"] = []
    # 初始化在线搜索的URL列表为空列表
    # 这个列表将存储搜索过程中访问的网页链接
    
    context["online_steps"] = []
    # 初始化处理步骤记录列表
    # 用于记录AI思考和处理的每个步骤
    
    context["online_answer"] = ""
    # 初始化最终答案为空字符串
    # 这里将存储AI生成的完整回答
    
    context["online_code_results"] = []
    # 初始化代码执行结果列表
    # 如果AI需要执行代码（如生成图表），结果会存储在这里
    
    context["online_answer_stars"] = None
    # 初始化答案评分为None
    # 这个功能目前可能还没有实现，预留给未来的评分系统

    queue = Queue()
    # 创建一个标准的线程安全队列
    # 这个队列用于在主线程和工作线程之间传递消息
    
    api_queue = WrapperQueue(queue)
    # 将标准队列包装成WrapperQueue
    # WrapperQueue提供了更方便的方法来处理消息
    
    thread = threading.Thread(
        target=deepresearch_workflow.run, 
        args=(query, WrapperQueue(), api_queue, LANGUAGE), 
        kwargs={"context": context}
    )
    # 创建一个新线程来执行深度研究工作流
    # 
    # 详细参数说明：
    # - target: 要在线程中执行的函数 线程里要执行的函数，就是工作流入口
    # - args: 位置参数的元组，传递给target函数
    #   * query: 用户的问题
    #   * WrapperQueue(): 一个新的空队列（none） 表示这路不启用
    #   * api_queue: 用于向API客户端发送消息的队列
    #   * LANGUAGE: 语言设置
    # - kwargs: 关键字参数的字典
    #   * context: 包含所有处理数据的上下文字典
    
    thread.start()
    # 启动线程，开始执行deepresearch_workflow.run函数
    # 注意：线程启动后会立即返回，不会等待线程完成
    
    return StreamingResponse(generator(api_queue), media_type="text/event-stream")
    # 返回流式响应
    # 
    # 详细说明：
    # - StreamingResponse: FastAPI的流式响应类
    # - generator(api_queue): 将我们的生成器函数作为数据源
    # - media_type="text/event-stream": 设置响应的内容类型为SSE
    # 
    # 工作流程：
    # 1. 客户端发送请求
    # 2. 服务器启动后台线程处理
    # 3. 后台线程将结果放入队列
    # 4. 生成器从队列取出消息，转换为SSE格式
    # 5. 客户端实时接收到处理结果

@app.post("/v1/chat/completions")
# 定义第二个API端点，路径为"/v1/chat/completions"
# 这个路径是仿照OpenAI API的格式设计的
# 目的是让DeepLiterature可以作为OpenAI API的替代品使用

async def create_item(request: Request):
    # 定义处理"/v1/chat/completions"请求的异步函数
    # 注意：函数名和上面的重复了，但Python允许在不同装饰器下使用相同函数名
    
    json_post_raw = await request.json()
    # 异步获取请求的JSON数据
    # 这次期望的格式和OpenAI API相同：
    # {
    #     "model": "模型名称",
    #     "messages": [消息列表],
    #     "temperature": 0.7,
    #     "max_tokens": 2048,
    #     "stream": true
    # }
    
    model = json_post_raw.get("model", "deepresearch")
    # 获取模型名称，默认值为"deepresearch"
    # .get()的第二个参数是默认值，如果"model"字段不存在就使用这个值
    
    messages = json_post_raw.get("messages", [])
    # 获取消息列表，默认为空列表
    # messages应该是包含多个消息对象的列表，格式如：
    # [
    #     {"role": "system", "content": "系统提示"},
    #     {"role": "user", "content": "用户问题"}
    # ]
    
    temperature = json_post_raw.get("temperature", 0.7)
    # 获取温度参数，默认0.7
    # 温度控制AI回答的随机性：
    # - 0.0: 最确定性的回答
    # - 1.0: 平衡创造性和确定性
    # - 2.0: 最有创造性的回答
    
    max_tokens = json_post_raw.get("max_tokens", 2048)
    # 获取最大token数，默认2048
    # token是文本的基本单位，大约1个token=0.75个英文单词
    
    stream = json_post_raw.get("stream", False)
    # 获取是否流式输出的标志，默认False
    # 虽然获取了这个参数，但代码中实际总是使用流式输出

    user_content = ""
    # 初始化用户内容为空字符串
    
    for msg in messages:
        # 遍历消息列表，提取用户和系统消息
        
        if msg["role"] == "system":
            # 如果消息角色是"system"（系统消息）
            system_content = msg["content"]
            # 提取系统提示词内容
            # 注意：这里有个问题，system_content变量只在if块内定义
            # 如果没有system消息，后续使用会报错
            
        elif msg["role"] == "user":
            # 如果消息角色是"user"（用户消息）
            user_content = msg["content"]
            # 提取用户查询内容
            # 这里假设只有一条用户消息，如果有多条会被覆盖

    context = dict()
    # 创建上下文字典，和上面的/stream端点相同
    
    context['question'] = user_content
    # 存储用户问题（注意这里用的是user_content而不是query）
    
    context["online_url_lists"] = []
    # 初始化在线URL列表
    
    context["online_steps"] = []
    # 初始化步骤记录列表
    
    context["online_answer"] = ""
    # 初始化答案字符串
    
    context["online_code_results"] = []
    # 初始化代码结果列表
    
    context["online_answer_stars"] = None
    # 初始化答案评分

    queue = Queue()
    # 创建线程安全队列
    
    api_queue = WrapperQueue(queue)
    # 包装队列
    
    thread = threading.Thread(
        target=deepresearch_workflow.run, 
        args=(user_content, WrapperQueue(), api_queue, LANGUAGE), 
        kwargs={"context": context}
    )
    # 创建后台处理线程
    # 注意：这里第一个参数是user_content而不是query
    
    thread.start()
    # 启动线程
    
    return StreamingResponse(generator(api_queue), media_type="text/event-stream")
    # 返回流式响应，和上面完全相同



if __name__ == '__main__':
    # 这是Python的特殊语法，检查脚本是否被直接运行
    # 如果文件被直接执行（如python api.py），这个条件为True
    # 如果文件被其他脚本导入（如import api），这个条件为False
    
    uvicorn.run(app, host='0.0.0.0', port=36668, workers=1, timeout_keep_alive=60)
    # 启动uvicorn服务器来运行FastAPI应用
    # 
    # 详细参数说明：
    # - app: 要运行的FastAPI应用实例
    # - host='0.0.0.0': 监听地址
    #   * '0.0.0.0'表示监听所有网络接口
    #   * 可以通过localhost、127.0.0.1或局域网IP访问
    #   * 如果设置为'127.0.0.1'则只能本机访问
    # - port=36668: 监听端口号
    #   * 客户端需要访问http://服务器IP:36668
    #   * 端口号可以是1024-65535之间的任意值
    # - workers=1: 工作进程数
    #   * 1表示只使用一个进程
    #   * 多进程可以提高并发处理能力，但会增加内存使用
    # - timeout_keep_alive=60: 保持连接的超时时间（秒）
    #   * 如果60秒内没有新请求，连接会被关闭
    #   * 对于流式应用，这个值应该设置得较大
