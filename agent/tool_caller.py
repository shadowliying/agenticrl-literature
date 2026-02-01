import json
from typing import Dict, List, Any, Optional, Union
import logging

from tools.tool_registry import registry
from tools.base_tool import BaseTool

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ToolCaller")

class ToolCaller:
    """工具调用接口，负责解析LLM的函数调用请求并执行相应的工具"""
    
    def __init__(self, tool_registry=registry):
        self.registry = tool_registry
    
    def get_tool_schemas(self) -> List[Dict]:
        """获取所有工具的JSON Schema定义，用于LLM的function calling"""
        return self.registry.get_tool_schemas()
    
    def parse_and_execute(self, function_call: Dict) -> Dict:
        """
        解析LLM的函数调用请求并执行相应的工具
        
        参数:
            function_call: LLM生成的函数调用请求，格式如下:
            {
                "name": "工具名称",
                "arguments": "JSON字符串格式的参数"
            }
            
        返回:
            工具执行结果
        """
        try:
            # 解析函数调用
            tool_name = function_call.get("name")
            arguments_str = function_call.get("arguments", "{}")
            
            # 检查工具是否存在
            tool = self.registry.get_tool(tool_name)
            if not tool:
                return {"error": f"工具 '{tool_name}' 不存在"}
            
            # 解析参数
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                return {"error": f"无法解析参数: {arguments_str}"}
            
            # 执行工具
            logger.info(f"执行工具: {tool_name}, 参数: {arguments}")
            result = tool.run(**arguments)
            logger.info(f"工具执行完成: {tool_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"工具执行失败: {e}", exc_info=True)
            return {"error": f"工具执行失败: {str(e)}"}
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict:
        """
        直接执行指定的工具
        
        参数:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        返回:
            工具执行结果
        """
        try:
            # 检查工具是否存在
            tool = self.registry.get_tool(tool_name)
            if not tool:
                return {"error": f"工具 '{tool_name}' 不存在"}
            
            # 执行工具
            logger.info(f"执行工具: {tool_name}, 参数: {kwargs}")
            result = tool.run(**kwargs)
            logger.info(f"工具执行完成: {tool_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"工具执行失败: {e}", exc_info=True)
            return {"error": f"工具执行失败: {str(e)}"}
    
    def batch_execute(self, function_calls: List[Dict]) -> List[Dict]:
        """
        批量执行多个工具调用
        
        参数:
            function_calls: LLM生成的函数调用请求列表
            
        返回:
            工具执行结果列表
        """
        results = []
        for function_call in function_calls:
            result = self.parse_and_execute(function_call)
            results.append({
                "tool_name": function_call.get("name"),
                "result": result
            })
        return results


# 创建全局工具调用器实例
tool_caller = ToolCaller() 