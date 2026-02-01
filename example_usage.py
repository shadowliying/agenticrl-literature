#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepLiterature使用示例
展示API调用和Web界面的区别
"""

import requests
import json
import time

def example_api_call():
    """
    示例：通过API接口调用DeepLiterature
    模拟一个客户端程序调用AI服务
    """
    print("=== API调用示例 ===")
    print("启动API服务：python src/service/api.py")
    print("服务地址：http://localhost:36668")
    print()
    
    # 构造请求数据（兼容OpenAI格式）
    request_data = {
        "model": "deepresearch",
        "messages": [
            {"role": "user", "content": "什么是机器学习？请给出详细解释"}
        ],
        "stream": True,  # 启用流式响应
        "temperature": 0.7,
        "max_tokens": 2048
    }
    
    print("发送请求...")
    print(f"请求数据：{json.dumps(request_data, ensure_ascii=False, indent=2)}")
    print()
    
    try:
        # 发送POST请求到API端点
        response = requests.post(
            'http://localhost:36668/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'
            },
            json=request_data,
            stream=True,  # 启用流式接收
            timeout=300   # 5分钟超时
        )
        
        print("接收流式响应...")
        print("=" * 50)
        
        # 处理流式响应
        full_answer = ""
        reasoning_content = ""
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                
                # SSE格式：data: JSON数据
                if line.startswith('data: '):
                    data = line[6:]  # 移除'data: '前缀
                    
                    # 检查是否结束
                    if data == '[DONE]':
                        print("\n" + "=" * 50)
                        print("响应完成")
                        break
                    
                    # 检查是否错误
                    if data == '[ERROR]':
                        print("发生错误")
                        break
                    
                    try:
                        # 解析JSON响应
                        json_data = json.loads(data)
                        
                        # 获取增量内容
                        choices = json_data.get('choices', [])
                        if choices:
                            delta = choices[0].get('delta', {})
                            
                            # 思考过程
                            if 'reasoning_content' in delta:
                                reasoning_part = delta['reasoning_content']
                                reasoning_content += reasoning_part
                                print(f"[思考] {reasoning_part}", end='', flush=True)
                            
                            # 答案内容
                            if 'content' in delta:
                                content_part = delta['content']
                                full_answer += content_part
                                print(content_part, end='', flush=True)
                                
                    except json.JSONDecodeError:
                        # 忽略无法解析的行
                        pass
        
        print(f"\n\n完整答案：\n{full_answer}")
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败：{e}")
        print("请确保API服务已启动：python src/service/api.py")

def example_web_interface():
    """
    示例：Web界面使用说明
    """
    print("\n=== Web界面使用示例 ===")
    print("启动Web服务：streamlit run src/service/platform_server.py --server.port 8501")
    print("访问地址：http://localhost:8501")
    print()
    
    print("界面功能说明：")
    print("1. 聊天输入框：在底部输入您的问题")
    print("2. 实时思考过程：AI会显示详细的思考和搜索过程")
    print("3. 代码执行：如果需要计算或画图，会显示代码和结果")
    print("4. JSON下载：可以下载完整的对话记录")
    print()
    
    print("数据流转过程：")
    print("用户输入 → Streamlit界面 → 后台线程 → AI工作流")
    print("AI工作流 → queue队列 → 主线程 → 界面实时更新")

def compare_two_approaches():
    """
    比较两种使用方式的区别
    """
    print("\n=== 两种方式对比 ===")
    
    comparison = [
        ["特性", "Web界面 (platform_server.py)", "API接口 (api.py)"],
        ["访问方式", "浏览器直接访问", "HTTP API调用"],
        ["用户界面", "可视化网页界面", "纯数据接口"],
        ["实时显示", "支持富文本、图片、代码高亮", "流式JSON数据"],
        ["使用场景", "普通用户交互使用", "程序集成、批量处理"],
        ["数据队列", "queue（界面指令）", "api_queue（标准格式）"],
        ["响应格式", "Streamlit组件", "SSE + JSON"],
        ["兼容性", "需要浏览器", "兼容OpenAI API格式"],
    ]
    
    # 打印表格
    for i, row in enumerate(comparison):
        if i == 0:
            print(f"{'|':<1} {row[0]:<20} | {row[1]:<35} | {row[2]:<35} |")
            print("|" + "-" * 95 + "|")
        else:
            print(f"{'|':<1} {row[0]:<20} | {row[1]:<35} | {row[2]:<35} |")

def workflow_explanation():
    """
    详细解释deepresearch_workflow.py的作用
    """
    print("\n=== AI工作流详细说明 ===")
    print("deepresearch_workflow.py是整个系统的大脑，负责：")
    print()
    
    print("1. 接收用户问题")
    print("2. 分析问题并制定搜索策略")
    print("3. 调用搜索引擎获取相关信息")
    print("4. 必要时生成和执行代码（如数据分析、画图）")
    print("5. 整合信息生成最终答案")
    print()
    
    print("两个队列的具体作用：")
    print()
    
    print("queue队列（给Web界面）：")
    print('- ["bar", "🤖 智能体 · 生成关键词"]  # 显示进度')
    print('- ["placeholder_think_stream_markdown", "思考内容"]  # 显示思考过程')  
    print('- ["code_result_text", "代码内容"]  # 显示代码')
    print('- ["code_result_image", base64_image]  # 显示图片')
    print('- ["finish", None]  # 结束信号')
    print()
    
    print("api_queue队列（给API接口）：")
    print('- format_data(reasoning_content="思考中...")  # 思考过程')
    print('- format_data(content="答案内容...")  # 回答内容')
    print('- format_data(finish=True)  # 结束信号')
    print()
    
    print("为什么要分两个队列？")
    print("- Web界面需要丰富的展示效果（Markdown、代码高亮、图片）")
    print("- API接口需要标准化的数据格式（兼容OpenAI API）")
    print("- 两种使用场景有不同的需求和数据处理方式")

if __name__ == "__main__":
    print("DeepLiterature 系统架构和使用说明")
    print("=" * 60)
    
    # 比较两种方式
    compare_two_approaches()
    
    # 详细解释工作流
    workflow_explanation()
    
    # Web界面示例
    example_web_interface()
    
    # API调用示例
    print("\n是否要测试API调用？(需要先启动API服务)")
    choice = input("输入 'y' 来测试API调用，其他键跳过: ").strip().lower()
    
    if choice == 'y':
        example_api_call()
    else:
        print("跳过API测试")
        print("\n如要测试，请先运行：python src/service/api.py")
        print("然后重新运行此脚本并选择测试API") 