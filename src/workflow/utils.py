# encoding: utf-8
# 文件编码声明，指定使用UTF-8编码，这样可以正确处理中文字符

# 导入标准库模块
import io          # 用于处理输入输出流，特别是内存中的字符串和字节流
import base64      # 用于base64编码和解码，常用于图像数据的编码传输
import time        # 用于时间相关操作，如获取当前时间戳、计算耗时等
import concurrent.futures  # 用于并发执行，可以创建线程池或进程池来并行处理任务
import json        # 用于JSON格式数据的序列化和反序列化
import re          # 正则表达式模块，用于字符串模式匹配和替换
import requests    # HTTP请求库，用于发送网络请求
import shortuuid   # 生成短UUID的库，用于创建唯一标识符

# 从项目内部模块导入所需的组件
from agents import CodeAgent, OrchestratorAgent  # 导入代码智能体和编排智能体
from tools.executors import CodeExecutor, SearchExecutor  # 导入代码执行器和搜索执行器
from config import JINA_API_KEY, JINA_API_URL, LANGUAGE  # 导入配置文件中的API密钥、URL和语言设置
from utils.message_queue import WrapperQueue  # 导入消息队列包装器，用于异步消息传递
from utils.logger import model_logger  # 导入模型日志记录器


# 定义mclick工具的JSON schema，这是一个函数调用工具的配置
mclick_tool = {
    "type": "function",  # 声明这是一个函数类型的工具
    "function": {
        "name": "mclick",  # 工具名称
        # 工具描述：说明何时使用这个工具，用于深入获取URL链接的详细内容
        "description": "当你获取的信息包含 link 的 URL 信息并希望深入获取更详细的内容时，使用此功能。将所有需要解析的 URL 根据 idx 形成索引列表，解析每个索引对应的 URL 并提取主要的文本信息。",
        "parameters": {  # 参数配置
            "type": "object",  # 参数类型为对象
            "properties": {  # 具体的属性定义
                "idx_list": {  # 索引列表参数
                    "type": "array",  # 数组类型
                    "items": {
                        "type": "integer"  # 数组元素为整数类型
                    },
                    "description": "需要检索网页的索引 (idx) 列表。"  # 参数说明
                },
                "tags": {  # HTML标签参数
                    "type": "array",  # 数组类型
                    "items": {
                        "type": "string"  # 数组元素为字符串类型
                    },
                    # 默认提取这些HTML标签的文本内容（段落和各级标题）
                    "description": "要提取文本的HTML标签列表。默认值为['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']。"
                },
                "include_links": {  # 是否包含链接参数
                    "type": "boolean",  # 布尔类型
                    "description": "是否在提取的文本中包含超链接。默认值为False。",
                    "default": False  # 默认不包含链接
                },
                "clean": {  # 是否清理参数
                    "type": "boolean",  # 布尔类型
                    "description": "是否在解析返回文本之前，去除脚本、样式和其他非文本元素。默认值为True。",
                    "default": True  # 默认进行清理
                }
            },
            "required": [  # 必需参数列表
                "idx_list"  # 只有索引列表是必需的
            ]
        }
    }
}

# 定义webSearch工具的JSON schema
webSearch_tool = {
    "type": "function",  # 声明这是一个函数类型的工具
    "function": {
        "name": "webSearch",  # 工具名称
        # 工具描述：说明何时使用这个搜索工具，适用于快速获取主题概述
        "description": "通过搜索引擎检索相关的页面的摘要或完整内容，适用于快速获取主题的简明概述。当你需要权威的简短总结而不需要深入分析或实时信息时，可以使用此功能。不适用于翻译或需要更详细、多样化的信息源的情况。",
        "parameters": {  # 参数配置
            "type": "object",  # 参数类型为对象
            "properties": {  # 具体的属性定义
                "keyword": {  # 关键词参数
                    "type": "string",  # 字符串类型
                    "description": "在网页上搜索的主要关键词或主题。"  # 参数说明
                },
                "max_results": {  # 最大结果数参数
                    "type": "integer",  # 整数类型
                    "description": "要检索的相关页面的最大数量。适用于限制搜索范围。",
                    "default": 10  # 默认返回10个结果
                }
            },
            "required": [  # 必需参数列表
                "keyword"  # 关键词是必需的
            ]
        }
    }
}

# 定义CodeRunner工具的JSON schema，用于执行Python代码
codeRunner_tool = {
    "type": "function",  # 声明这是一个函数类型的工具
    "function": {
        "name": "CodeRunner",  # 工具名称
        # 工具描述：详细说明代码执行工具的功能和使用场景
        "description": "This Plugin will be called to run python code and fetch results within 60s, especially processing math, computer, picture and file etc. Firstly, LLM will analyse the problem and output the steps of solving this problem with python. Secondly, LLM generates code to solve problems with steps immediately. LLM will adjust code referring to the error message until success. When LLM receives file links, put the file url and the file name in the parameter upload_file_url and upload_file_name, the plugin will save it to \"/mnt/data\", alse put code in the parameter code to output file basic info.",
        "parameters": {  # 参数配置
            "type": "object",  # 参数类型为对象
            "properties": {  # 具体的属性定义
                "code": {  # 代码参数
                    "description": "code",  # 要执行的Python代码
                    "type": "string"  # 字符串类型
                },
                "upload_file_name": {  # 上传文件名参数
                    "description": "save the upload_file_url with the corresponding filename.",
                    "type": "string"  # 字符串类型
                },
                "upload_file_url": {  # 上传文件URL参数
                    "description": "when recieve file link, then the plugin will save it to \"/mnt/data\"",
                    "type": "string"  # 字符串类型
                }
            },
            "required": [  # 必需参数列表
                "code"  # 代码是必需的
            ]
        }
    }
}


# 定义run_code函数：执行代码生成和运行的完整流程
def run_code(code_agent: CodeAgent, code_executor: CodeExecutor, meta_data, all_steps, step_idx, question, previous_reference, reference_list, verbose=False, context=dict(), queue=WrapperQueue(), api_queue=WrapperQueue(), request_id=None):
    """
    执行代码生成和运行的函数
    
    参数说明：
    - code_agent: 代码智能体，负责生成代码
    - code_executor: 代码执行器，负责运行代码
    - meta_data: 元数据信息
    - all_steps: 所有步骤的列表
    - step_idx: 当前步骤的索引
    - question: 用户提出的问题
    - previous_reference: 之前的参考信息
    - reference_list: 参考信息列表
    - verbose: 是否输出详细信息
    - context: 上下文字典
    - queue: 消息队列
    - api_queue: API消息队列
    - request_id: 请求ID
    """
    # 从当前步骤中获取关键词列表
    now_step_keywords = all_steps[step_idx]['now_step_keywords']
    # 初始化存储所有生成代码的列表
    all_codes = []
    # 初始化存储所有代码执行结果的列表
    all_code_results = []
    
    # 如果开启详细模式，则处理每个关键词
    if verbose:
        # 遍历当前步骤的每个关键词
        for new_keyword in now_step_keywords:
            # 生成对应的代码
            # 向队列发送进度信息，显示正在生成代码
            queue.put(["bar", f"🐍 智能体 · 生成代码：\n:grey-background[{new_keyword}]"])
            # 将进度信息添加到上下文中
            context["online_steps"].append(f"🐍 智能体 · 生成代码：\n:grey-background[{new_keyword}]")
            
            # 初始化占位符变量，用于管理流式输出
            placeholder_think = None  # 思考过程的占位符
            placeholder_answer = None  # 答案的占位符
            _reasoning_content = ""  # 存储推理内容
            now_code = ""  # 存储当前生成的代码
            
            # 获取当前的消息列表
            now_messages = meta_data.get("messages", [])
            # 记录当前消息列表的长度
            cur_size = len(now_messages)
            
            # 调用代码智能体生成代码，返回流式输出
            for label, _stream_text in code_agent.run(question, new_keyword, previous_reference, reference_list):
                # 处理思考过程的流式输出
                if label == "think":
                    # 累积推理内容
                    _reasoning_content += _stream_text
                    # 如果是第一次输出思考内容，创建占位符
                    if placeholder_think is None:
                        queue.put(["placeholder_begin", None])
                        context["online_steps"].append("")
                        placeholder_think = "placeholder_begin"
                    # 更新思考内容的Markdown显示
                    queue.put(["placeholder_think_stream_markdown", convert_think_message_to_markdown(_reasoning_content)])
                    context["online_steps"][-1] = convert_think_message_to_markdown(_reasoning_content)
                    # 向API队列发送推理内容
                    api_queue.put(format_data(reasoning_content=_stream_text, id=request_id, stage="create code"))
                # 处理答案（代码）的流式输出
                elif label == "answer":
                    # 累积代码内容
                    now_code += _stream_text
                    # 如果是第一次输出代码，创建占位符
                    if placeholder_answer is None:
                        queue.put(["placeholder_begin", None])
                        context["online_steps"].append("")
                        placeholder_answer = "placeholder_begin"
                    # 更新代码内容的纯文本显示
                    queue.put(["placeholder_answer_plain_text", now_code])
                    context["online_steps"][-1] = now_code
                    # 向API队列发送代码内容
                    api_queue.put(format_data(content=_stream_text, id=request_id, stage="create code"))
                # 处理最终答案
                elif label == "final_answer":
                    # 设置最终的代码内容
                    now_code = _stream_text
            
            # 将完整的消息（包含推理过程和代码）添加到消息列表
            now_messages.append({"reasoning_content": _reasoning_content, "content": now_code, "role": "assistant", "stage": "create code"})
            # 以Markdown格式显示最终代码
            queue.put(["placeholder_answer_markdown", f"""```python\n\n{now_code}\n\n```"""])
            context["online_steps"][-1] = """```python\n\n{now_code}\n\n```"""
            # 将代码添加到所有代码列表中
            all_codes.append(now_code)
            # 将完整的代码生成信息添加到上下文中
            context["online_steps"].append(f"🐍 智能体 · 生成代码：\n:grey-background[{new_keyword}]\n\n" + "```python\n\n" + now_code + "\n\n```")
            
            # 执行代码
            # 创建新的占位符用于显示执行状态
            queue.put(["placeholder_begin", None])
            queue.put(["placeholder_caption", "⏳ 调工具 · 代码执行中..."])
            context["online_steps"].append("⏳ 调工具 · 代码执行中...")
            
            # 使用代码执行器执行生成的代码
            code_results = code_executor.execute(now_code)
            # 将执行结果添加到结果列表中
            all_code_results.append(code_results)
            
            # 显示代码执行结果
            queue.put(["placeholder_bar", "📊 调工具 · 代码结果为："])
            context["online_steps"].append("📊 调工具 · 代码结果为：")
            
            # 添加代码执行结果的消息
            now_messages.append({"content": "", "img": "", "role": "assistant", "stage": "run code and get result"})
            # 向API队列发送分隔符
            api_queue.put(format_data(content="-"*20 + "\n\n", id=request_id, stage="run code and get result"))
            
            # 返回代码结果
            # 遍历所有代码执行结果
            for code_result in code_results:
                # 如果结果包含文本内容
                if "text" in code_result:
                    # 显示文本结果
                    queue.put(["code_result_text", code_result['text']])
                    context["online_steps"].append(code_result)
                    # 更新消息内容
                    now_messages[-1]["content"] = code_result['text']
                    # 向API队列发送文本内容
                    api_queue.put(format_data(content=code_result['text'] + "\n\n", id=request_id, stage="run code and get result"))
                # 如果结果包含图像
                if "img" in code_result:
                    # 显示图像结果
                    queue.put(["code_result_image",code_result['img']])
                    context["online_steps"].append(code_result)
                    # 更新消息的图像内容（注意这里有个拼写错误，应该是"img"而不是"imge"）
                    now_messages[-1]["imge"] = code_result['img']
                    # 向API队列发送图像信息
                    api_queue.put(format_data(content="img:\n\n"+ str(code_result['img']) + "\n\n", id=request_id, stage="run code and get result"))

    # 添加分隔符，表示这个步骤完成
    queue.put(["divider", None])
    context["online_steps"].append("\n---\n")

    # 返回所有生成的代码和执行结果
    return all_codes,all_code_results

# 定义fetch_search_result函数：获取搜索结果
def fetch_search_result(all_steps, step_idx, old_raw_info, verbose=False, search_type="wiki", context=dict(), queue=WrapperQueue()):
    """
    获取搜索结果的函数
    
    参数说明：
    - all_steps: 所有步骤列表
    - step_idx: 当前步骤索引
    - old_raw_info: 之前的原始信息
    - verbose: 是否输出详细信息
    - search_type: 搜索类型（默认为wiki）
    - context: 上下文字典
    - queue: 消息队列
    """
    # 记录开始时间，用于计算耗时
    start_time = time.time()
    # 获取当前步骤的关键词列表
    now_step_keywords = all_steps[step_idx]['now_step_keywords']
    # 获取当前步骤关键词的索引列表
    now_step_keyword_idxs = all_steps[step_idx]['now_step_keyword_idxs']
    
    # 如果开启详细模式，显示搜索进度
    if verbose:
        # 构建显示文本，将所有关键词用灰色背景标出
        render_text = ""
        for new_keyword in now_step_keywords:
            render_text += ":grey-background[" + new_keyword + "] "
        # 向队列发送关键词生成信息
        queue.put(["bar", "🤖 智能体 · 生成关键词：" + render_text])
        context["online_steps"].append("🤖 智能体 · 生成关键词：" + render_text)
        # 向队列发送搜索引擎调用信息
        queue.put(["bar", "🔍 调工具 · 搜索引擎"])
        context["online_steps"].append("🔍 调工具 · 搜索引擎")
    
    # 构建新的 raw_info 
    # 新位置开始的 index
    start_index = now_step_keyword_idxs[0]  # 获取新搜索开始的索引位置
    start_doc_idx = 0  # 初始化文档索引计数器
    new_raw_info = []  # 初始化新的原始信息列表
    
    # 保留之前的搜索结果
    for raw_idx, raw_info in enumerate(old_raw_info):
        # 之前的所有 raw_info 直接保留
        if raw_idx < start_index:
            new_raw_info.append(raw_info)
            start_doc_idx += len(raw_info)  # 累加文档数量

    # 用于去重的标题集合
    new_titles = set()
    # 记录空搜索的数量
    is_empty_search = 0
    # 创建搜索执行器
    search_executor = SearchExecutor(search_type)
    
    # 使用线程池并发执行多个搜索任务
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 存储所有异步任务的列表
        futures = []
        # 为每个关键词提交搜索任务
        for new_keyword in now_step_keywords:
            futures.append(executor.submit(search_executor.execute, new_keyword, verbose))

        # 处理已完成的搜索任务
        for future in concurrent.futures.as_completed(futures):
            # 获取搜索结果：关键词、是否空搜索、搜索结果
            new_keyword, empty_search, new_keyword_search_res = future.result()
            # 如果搜索不为空
            if not empty_search:
                # 显示搜索结果浏览信息
                queue.put(["bar", f"🧐 智能体 · 浏览关键词 :grey-background[{new_keyword}] 的搜索结果："])
                context["online_steps"].append(f"🧐 智能体 · 浏览关键词 :grey-background[{new_keyword}] 的搜索结果：")
                context["online_steps"].append([])
                # 创建容器开始标记，设置高度为200像素
                queue.put(["container_begin", {"height":200}])
                # 处理每个搜索结果
                for now_info_idx, now_info in enumerate(new_keyword_search_res):
                    # 清理标题中的换行符，避免显示问题
                    new_keyword_search_res[now_info_idx]['title'] = new_keyword_search_res[now_info_idx]['title'].replace("\n", " ")
                    # 格式化消息，包含索引、标题、链接和摘要
                    msg = "📃{idx} - {title} - 🔗 [click]({url}) \n> :grey[{snippet}]\n\n".format(
                        idx=int(start_doc_idx + now_info_idx) + 1, 
                        title=new_keyword_search_res[now_info_idx]['title'], 
                        url=new_keyword_search_res[now_info_idx]['url'], 
                        snippet=new_keyword_search_res[now_info_idx].get("snippet")
                    )
                    # 发送容器内容
                    queue.put(["container_content", msg])
                    context["online_steps"][-1].append(msg)
            else:
                # 如果搜索失败，显示警告信息
                queue.put(["bar", f"⚠️ 调工具 · 搜索关键词 :grey-background[{new_keyword}] 失败"])
                context["online_steps"].append(f"⚠️ 调工具 · 搜索关键词 :grey-background[{new_keyword}] 失败")
                is_empty_search += 1  # 增加空搜索计数

            # 添加新的检索结果到列表中
            new_raw_info.append(new_keyword_search_res)
            start_doc_idx += len(new_keyword_search_res)  # 更新文档索引
            # 收集所有新的标题用于去重
            for search_doc in new_keyword_search_res:
                new_title = search_doc['title']
                new_titles.add(new_title)

    # 添加分隔符
    queue.put(["divider", None])
    context["online_steps"].append("\n---\n")
    # 将标题集合转换为列表
    new_titles = list(new_titles)

    # 打印日志
    # 判断是否为空搜索：如果超过一半的关键词搜索失败，则认为是空搜索
    empty_search = True if is_empty_search > len(now_step_keywords)/2 else False
    # 构建输入输出日志信息
    in_out = {"state": "update_raw_info", 
              "input": {"all_steps": all_steps, "step_idx":step_idx, "old_raw_info": old_raw_info, "verbose": verbose,  "search_type": search_type}, 
              "output": {"empty_search": empty_search, "new_raw_info":new_raw_info}, 
              "cost_time": str(round(time.time()-start_time, 3))}
    # 记录日志
    model_logger.info(json.dumps(in_out, ensure_ascii=False))
    return empty_search, new_raw_info

# 定义process_message函数：处理消息格式化
def process_message(content = "",role = "system", tool_calls = [] , tool_call_id = "", result_list = [], content_ref = ""):
    """
    处理和格式化消息的函数
    
    参数说明：
    - content: 消息内容
    - role: 角色（system, user, assistant等）
    - tool_calls: 工具调用列表
    - tool_call_id: 工具调用ID
    - result_list: 结果列表
    - content_ref: 内容引用
    """
    # 初始化消息字典
    message = {}
    # 设置消息内容
    message['content'] = content
    # 如果有内容引用，添加到消息中
    if len(content_ref) > 0:
        message['content_ref'] = content_ref
    # 设置角色
    message['role'] = role
    # 如果有工具调用，添加到消息中
    if len(tool_calls) > 0:
        message['tool_calls'] = tool_calls
    # 如果有工具调用ID，添加到消息中
    if len(tool_call_id) > 0:
        message['tool_call_id'] = tool_call_id
    
    # 如果有结果列表，添加到消息中
    if len(result_list) > 0:
        message['result_list'] = result_list

    return message

# 定义generate_call_id函数：生成唯一的调用ID
def generate_call_id():
    """
    生成唯一调用ID的函数
    """
    # 生成短UUID
    short_uuid = shortuuid.uuid()
    # 自定义格式化，例如添加前缀和截取部分字符
    custom_id = f"call_{short_uuid[:24]}"  # 取前24个字符并添加"call_"前缀
    return custom_id

# 定义get_tool_list函数：根据使用记录获取工具列表
def get_tool_list(use_tool_record):
    """
    根据工具使用记录获取可用工具列表的函数
    
    参数说明：
    - use_tool_record: 工具使用记录字典
    """
    tool_list = []  # 初始化工具列表
    # 根据记录中的工具名称添加对应的工具配置
    if "webSearch" in use_tool_record:
        tool_list.append(webSearch_tool)
    if "mclick" in use_tool_record:
        tool_list.append(mclick_tool)
    if "codeRunner" in use_tool_record:
        tool_list.append(codeRunner_tool)
    return tool_list

# 定义count_token函数：计算文本的token数量
def count_token(tokenizer, text):
    """
    计算文本token数量的函数
    
    参数说明：
    - tokenizer: 分词器对象
    - text: 要计算的文本
    """
    # 使用分词器对文本进行编码，返回PyTorch张量格式
    now_inputs = tokenizer([text], return_tensors="pt")
    # 返回input_ids的长度，即token数量
    return len(now_inputs['input_ids'][0])

# 定义step_by_step_process函数：处理步骤化搜索流程（第一个版本，似乎是重复定义）
def step_by_step_process(search_process):
    """
    处理步骤化搜索流程的函数（第一个版本）
    
    参数说明：
    - search_process: 搜索流程字符串
    """
    # 如果包含"->"符号，按该符号分割步骤
    if "->" in search_process:
        stage_list = [stage.strip() for stage in search_process.split("->")]
    else:
        stage_list = [search_process.strip()] # 说明是单步的

    # 找出关键阶段的起始和结束位置
    key_stage = []  # 存储关键阶段的起止索引
    start = -1  # 起始位置
    end = -1    # 结束位置
    
    # 遍历所有阶段，识别包含webSearch的阶段
    for idx, stage in enumerate(stage_list):
        if "webSearch" in stage:
            start = idx
            if end < start:
                end = start
        else:
            end = idx
            key_stage.append([start,end])  # 添加一个完整的阶段
            start = idx + 1
            end = idx + 1
    # 处理最后一个阶段
    if start == end and start != -1:
        key_stage.append([start,end])
  

    step_process = []  # 存储处理后的步骤
    step_chain = ""    # 步骤链字符串
    keyword_idx = 0    # 关键词索引计数器
    
    # 处理每个关键阶段
    for start_end in key_stage:
        now_start = start_end[0]  # 当前阶段起始位置
        now_end = start_end[1]    # 当前阶段结束位置
        # 构建步骤链字符串
        step_chain = " -> ".join(stage_list[now_start: now_end + 1])
        # 解析关键词
        now_keywords = OrchestratorAgent.parse_keywords(" -> ".join(stage_list[now_start: now_end + 1]))
        # 生成关键词索引列表
        now_idxs = [keyword_idx + i for i in range(len(now_keywords))]
        keyword_idx += len(now_keywords)  # 更新关键词索引计数器
        # 构建步骤信息字典
        tmp = {
            "step_desc": step_chain,
            "now_step_keywords": now_keywords,
            "now_step_keyword_idxs" : now_idxs
        }
        step_process.append(tmp)

    return step_process

# 定义step_by_step_process函数：处理步骤化搜索流程（第二个版本，覆盖了第一个）
def step_by_step_process(search_process):
    """
    处理步骤化搜索流程的函数（第二个版本，增强版）
    
    参数说明：
    - search_process: 搜索流程字符串
    """
    # 只取第一段内容，忽略后面的空行
    search_process = search_process.split("\n\n")[0]
    
    # 将 search_process 加工成多步的，后面的步骤需要 mask 掉
    # 支持两种箭头符号："->" 和 "→"
    if "->" in search_process:
        stage_list = [stage.strip() for stage in search_process.split("->")]
    elif "→" in search_process:
        stage_list = [stage.strip() for stage in search_process.split("→")]
    else:
        stage_list = [search_process.strip()] # 说明是单步的

    # 找出关键阶段
    key_stage = []
    start = -1
    end = -1
    
    # 遍历所有阶段，识别包含webSearch或codeRunner的阶段
    for idx, stage in enumerate(stage_list):
        if "webSearch" in stage or "codeRunner" in stage:
            # 处理上一个还是关键词的情况
            if start == end and end != -1 and start != idx:
                key_stage.append([start,end])
            start = idx
            if end < start:
                end = start
        else:
            end = idx
            key_stage.append([start,end])
            start = idx + 1
            end = idx + 1
    # 处理最后一个阶段
    if start == end and start != -1:
        key_stage.append([start,end])
  
    step_process = []
    step_chain = ""
    keyword_idx = 0
    
    # 处理每个关键阶段（与第一个版本相同的逻辑）
    for start_end in key_stage:
        now_start = start_end[0]
        now_end = start_end[1]
        step_chain = " -> ".join(stage_list[now_start: now_end + 1])
        now_keywords = OrchestratorAgent.parse_keywords(" -> ".join(stage_list[now_start: now_end + 1]))
        now_idxs = [keyword_idx + i for i in range(len(now_keywords))]
        keyword_idx += len(now_keywords)
        tmp = {
            "step_desc": step_chain,
            "now_step_keywords": now_keywords,
            "now_step_keyword_idxs" : now_idxs
        }
        step_process.append(tmp)

    return step_process

# 定义function_call_sent函数：发送函数调用消息
def function_call_sent(argument_values_list, call_ids, function_name = "wikiSearch", argument_names = ["keyword"], content = ""):
    """
    发送函数调用消息的函数
    
    参数说明：
    - argument_values_list: 参数值列表
    - call_ids: 调用ID列表
    - function_name: 函数名称（默认为wikiSearch）
    - argument_names: 参数名称列表（默认为["keyword"]）
    - content: 消息内容
    """
    tool_calls = []  # 初始化工具调用列表
    
    # 为每个参数值和调用ID创建工具调用
    for argument_values, call_id in zip(argument_values_list, call_ids):
        arguments = {}  # 初始化参数字典
        # 将参数名和参数值配对
        for argument_name, argument_value  in zip(argument_names, argument_values):
            arguments[argument_name] = argument_value
        
        # 构建工具调用字典
        tmp = {
            "id": call_id,
            "type": "function",
            "function": {
                "name": function_name,
                "arguments": json.dumps(arguments, ensure_ascii=False)  # 将参数序列化为JSON
            }
        }
        tool_calls.append(tmp)
    
    # 返回格式化的消息
    return process_message(role = "assistant", tool_calls=tool_calls, content = content)

# 定义function_call_receive_code_results函数：接收代码执行结果
def function_call_receive_code_results(now_step_keywords, all_codes, call_ids, raw_code_results):
    """
    接收和处理代码执行结果的函数
    
    参数说明：
    - now_step_keywords: 当前步骤关键词列表
    - all_codes: 所有代码列表
    - call_ids: 调用ID列表
    - raw_code_results: 原始代码执行结果
    """
    now_messages = []  # 存储当前消息列表
    evidences = []     # 存储证据列表
    
    # 处理每个原始代码结果
    for idx, raw_code_result in enumerate(raw_code_results):
        # 初始化代码结果文本列表，包含代码和结果标题
        code_result_text_list = ["Code:\n" + all_codes[idx] + "Result:\n"]
        img_idx = 1  # 图像索引计数器
        
        # 处理每个代码结果
        for code_idx, code_result in enumerate(raw_code_result):
            # 如果结果包含图像
            if "img" in code_result:
                # 添加图像的Markdown链接
                code_result_text_list.append(f"![fig-{img_idx}]({now_step_keywords[idx]}_result_{call_ids[idx]}_{img_idx}.png)")
                # 为原始结果添加图像索引和路径信息
                raw_code_result[code_idx]['img_idx'] = img_idx
                raw_code_result[code_idx]['img_path'] = f"{now_step_keywords[idx]}_result_{call_ids[idx]}_{img_idx}.png"
                img_idx += 1  # 增加图像索引
            else: 
                # 如果是文本结果，直接添加
                code_result_text_list.append(code_result['text'])
                
        # 创建工具调用响应消息
        now_messages.append(process_message(content = "\n\n".join(code_result_text_list), role = "tool", tool_call_id = call_ids[idx], result_list = raw_code_result))
        # 将结果添加到证据列表
        evidences.append("\n\n".join(code_result_text_list))
    
    return evidences, now_messages

# 定义function_call_receive_snippet函数：接收搜索摘要结果
def function_call_receive_snippet(keywords, call_ids, search_res, raw_info):
    """
    接收和处理搜索摘要结果的函数
    
    参数说明：
    - keywords: 关键词列表
    - call_ids: 调用ID列表
    - search_res: 搜索结果
    - raw_info: 原始信息
    """
    now_messages = []  # 存储当前消息列表
    
    # 处理每个关键词的搜索结果
    for idx, keyword in enumerate(keywords):
        document_list = []  # 存储文档列表
        
        # 处理该关键词的每个搜索结果
        for now_search in search_res[idx]:
            # 构建文档字典，包含标题、摘要和链接
            now_doc = {
                now_search['idx']:f"{now_search['title']}\nsnippet:{now_search['snippet']}\nlink:{now_search['url']}"
            }
            document_list.append(now_doc)
        
        # 创建工具调用响应消息
        now_messages.append(process_message(content = json.dumps(document_list, ensure_ascii=False), role = "tool", tool_call_id = call_ids[idx], result_list = raw_info[idx]))

    return now_messages

# 定义function_call_receive_document函数：接收完整文档内容
def function_call_receive_document(idx_list, call_ids, search_res, context=dict(), queue=WrapperQueue()):
    """
    接收和处理完整文档内容的函数
    
    参数说明：
    - idx_list: 索引列表
    - call_ids: 调用ID列表
    - search_res: 搜索结果
    - context: 上下文字典
    - queue: 消息队列
    """
    # 定义内部函数：接收单个文档
    def receive_document(url, idx, title):
        """
        接收单个文档内容的内部函数
        
        参数说明：
        - url: 文档URL
        - idx: 文档索引
        - title: 文档标题
        """
        return analysis_url_api(url), url, idx, title
    
    ii = 0  # 计数器（未使用）
    document_list = []  # 存储文档列表
    
    # 使用线程池并发获取多个文档
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []  # 存储异步任务
        
        # 为每个要获取的索引创建任务
        for mclick_idx in idx_list:
            # 遍历所有搜索结果，找到匹配的索引
            for now_search in search_res:
                for doc_info in now_search:
                    if str(doc_info['idx']) == str(mclick_idx):
                        # time.sleep(1)  # 注释掉的延时
                        # 提交文档获取任务
                        futures.append(executor.submit(receive_document, doc_info['url'], doc_info['idx'], doc_info['title']))
        
        # 创建容器开始标记，高度根据任务数量动态设置
        queue.put(["container_begin", {"height": min(len(futures) * 60, 200)}])
        
        # 获取所有任务的结果并将其添加到 document_list 列表中
        for future in concurrent.futures.as_completed(futures):
            # 获取解析结果、URL、索引和标题
            parse_response, now_url, now_idx, now_title = future.result()
            
            # 处理获取网页快照失败的情况
            if parse_response == "":
                # 如果解析失败，使用摘要作为内容
                parse_response = doc_info['snippet']
                # 显示无法打开的警告信息
                queue.put(["container_bar", f"⚠️ 调工具 · 打不开 :blue-background[📃{now_idx + 1} {now_title}]  - 🔗[click]({now_url} \"{now_url}\")"])
                context["online_steps"].append(f"⚠️ 调工具 · 打不开 :blue-background[📃{now_idx + 1} {now_title}]  - 🔗[click]({now_url} \"{now_url}\")")
            else:
                # 如果解析成功，显示阅读完毕信息
                queue.put(["container_bar", f"🤓 智能体 · 阅读完毕 :blue-background[📃{now_idx + 1} {now_title}]  - 🔗[click]({now_url} \"{now_url}\")"])
                context["online_steps"].append(f"🤓 智能体 · 阅读完毕 :blue-background[📃{now_idx + 1} {now_title}]  - 🔗[click]({now_url} \"{now_url}\")")
                    
                    
            # 构建文档字典
            now_doc = {
                # content 通过 URL 解析获得
                now_idx:f"{now_title}\n{parse_response}\nlink:{now_url}"
            }
            document_list.append(now_doc)
    
    # 添加分隔符
    queue.put(["divider", None])
    context["online_steps"].append("\n---\n")
    
    # 返回格式化的工具调用响应消息
    return process_message(content = json.dumps(document_list, ensure_ascii=False), role = "tool", tool_call_id = call_ids[ii])


# 定义update_search_res函数：更新搜索结果
def update_search_res(all_steps, step_idx, old_search_res, raw_infos, verbose=False, context=dict()):
    """
    更新搜索结果的函数
    
    参数说明：
    - all_steps: 所有步骤列表
    - step_idx: 当前步骤索引
    - old_search_res: 旧的搜索结果
    - raw_infos: 原始信息列表
    - verbose: 是否输出详细信息
    - context: 上下文字典
    """
    # 记录开始时间
    start_time = time.time()
    # 获取当前步骤的关键词和索引
    now_step_keywords = all_steps[step_idx]['now_step_keywords']
    now_step_keyword_idxs = all_steps[step_idx]['now_step_keyword_idxs']
    start_index = now_step_keyword_idxs[0]  # 获取起始索引
    new_search_res = []  # 新的搜索结果列表
    start_doc_idx = 0    # 文档索引起始位置
    
    # 更新 search_res
    # 保留之前的搜索结果
    for search_idx, search_res in enumerate(old_search_res):
        # 跳过之前的所有 search_res
        if search_idx < start_index:
            new_search_res.append(search_res)
            start_doc_idx += len(search_res)  # 累加文档数量

    # 处理新的原始信息
    for raw_idx, raw_info in enumerate(raw_infos):
        # 跳过之前已处理的信息
        if raw_idx < start_index:
            continue
        
        this_time_search = []  # 当前搜索的结果列表
        title_set = set()      # 用于标题去重的集合
        
        # 处理每个文档信息
        for i, doc_info in enumerate(raw_info):

            now_content = ""  # 当前内容（暂时为空）

            # 构建文档信息字典
            tmp = {
                "title": doc_info['title'],      # 文档标题
                'snippet': doc_info['snippet'],  # 文档摘要
                'content': now_content,          # 文档内容
                'url': doc_info['url'],          # 文档URL
                'idx': start_doc_idx,            # 文档索引
            }
            
            # 根据网页title去重
            if doc_info['title'] not in title_set:
                title_set.add(doc_info['title'])  # 添加到去重集合
                this_time_search.append(tmp)      # 添加到结果列表
                # 如果开启详细模式，添加到上下文
                if verbose:
                    context["online_url_lists"].append(tmp)
                start_doc_idx += 1  # 增加文档索引
            # 最多 10 篇文章
            if i == 9:
                break
        
        # 将这次搜索的结果添加到新搜索结果中
        new_search_res.append(this_time_search)

    # 记录日志信息
    in_out = {"state": "update_search_res", 
              "input": {"all_steps": all_steps, "step_idx":step_idx, "old_search_res": old_search_res, "verbose": verbose,  "raw_infos": raw_infos}, 
              "output": {"new_search_res": new_search_res}, 
              "cost_time": str(round(time.time()-start_time, 3))}
    model_logger.info(json.dumps(in_out, ensure_ascii=False))

    return new_search_res

# 定义find_special_text_and_numbers函数：查找特殊文本和数字
def find_special_text_and_numbers(text):
    """
    查找文本中特殊格式的引用标记和数字的函数
    
    参数说明：
    - text: 要搜索的文本
    
    返回：
    - special_texts: 特殊文本列表
    - number_lists: 数字列表的列表
    """
    # 定义正则表达式模式，匹配 ◥[数字]◤ 格式的引用标记
    # 支持逗号或中文逗号分隔的多个数字
    pattern = r'◥\[(\d+(?:[,\，]\s*\d+)*)\]◤'
    # 查找所有匹配项
    matches = re.findall(pattern, text)
    
    # 提取文本和数字列表
    # 重新构建特殊文本（用于后续替换）
    special_texts = [f'◥[{nums}]◤' for nums in matches]
    # 将数字字符串转换为整数列表
    number_lists = [[int(num) for num in re.split(r'[,\，]', nums)] for nums in matches]
    
    return special_texts, number_lists

# 定义remove_ref_tag函数：移除引用标签
def remove_ref_tag(origin_llm_answer):
    """
    从LLM回答中移除引用标签的函数
    
    参数说明：
    - origin_llm_answer: 原始LLM回答
    
    返回：
    - new_llm_answer: 移除引用标签后的回答
    """
    new_llm_answer = origin_llm_answer  # 复制原始回答
    # 查找特殊文本和数字
    special_texts, special_numbers = find_special_text_and_numbers(origin_llm_answer)
    
    # 移除所有特殊引用标记
    for special_id, numbers in enumerate(special_numbers):
        new_llm_answer = new_llm_answer.replace(special_texts[special_id], "")
    
    return new_llm_answer


# 定义analysis_url_api函数：通过API解析URL内容
def analysis_url_api(analysis_url):
    """
    通过Jina API解析URL内容的函数
    
    参数说明：
    - analysis_url: 要解析的URL
    
    返回：
    - 解析后的文本内容，失败时返回空字符串
    """
    # 构建API请求URL
    if JINA_API_URL.endswith("/"):
        url = f"{JINA_API_URL}{analysis_url}"
    else:
        url = f"{JINA_API_URL}/{analysis_url}"
    
    # 设置请求头，包含授权信息
    headers = {
    "Authorization": f"Bearer {JINA_API_KEY}"
    }

    # 发送GET请求
    response = requests.get(url, headers=headers)
    # 如果请求失败，返回空字符串
    if response.status_code != 200:
        return ""
    # 返回响应文本
    return response.text


# 定义convert_think_message_to_markdown函数：将思考消息转换为Markdown格式
def convert_think_message_to_markdown(message):
    """
    将思考过程消息转换为Markdown格式的函数
    
    参数说明：
    - message: 原始思考消息
    
    返回：
    - markdown_text: 格式化后的Markdown文本
    """
    # 按行分割消息
    lines = message.split("\n")
    
    # 根据语言设置选择标题
    if LANGUAGE == "zh":
        markdown_text = """> <font color=grey size=2>深度思考...</font><br>\n"""
    elif LANGUAGE == "en":
        markdown_text = """> <font color=grey size=2>Deep Thingking...</font><br>\n"""
    
    # 将每行都格式化为灰色小字体的引用块
    markdown_text += "<br>\n".join([f"""> <font color=grey size=2>{line}</font>""" for line in lines])
    return markdown_text


# 定义format_data函数：格式化数据为标准响应格式
def format_data(reasoning_content=None, content=None, id="", finish=False, **kwargs):
    """
    将数据格式化为标准响应格式的函数
    
    参数说明：
    - reasoning_content: 推理内容
    - content: 主要内容
    - id: 请求ID
    - finish: 是否完成
    - **kwargs: 其他关键字参数
    
    返回：
    - result: 格式化后的响应字典
    """
    # 构建基础响应结构
    result = {
        "id": id,                           # 请求ID
        "created": int(time.time()),        # 创建时间戳
        "choices": [                        # 选择列表
            {
                "index": 0,                 # 选择索引
                "delta": {}                 # 增量内容
            }
        ]
    }
    
    # 添加额外的关键字参数
    for key, item in kwargs.items():
        if key in result:
            continue  # 跳过已存在的键
        result[key] = item
    
    # 根据不同情况设置响应内容
    if finish:
        # 如果完成，设置完成原因
        result["choices"][0]["finish_reason"] = "stop"
    elif reasoning_content is not None:
        # 如果有推理内容，设置推理内容
        result["choices"][0]["delta"]["reasoning_content"] = reasoning_content
    elif content is not None:
        # 如果有主要内容，设置主要内容
        result["choices"][0]["delta"]["content"] = content
    
    return result