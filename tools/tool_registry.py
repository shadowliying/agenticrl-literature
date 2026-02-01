from typing import Dict, List, Type, Any, Optional
import importlib
import inspect
import os
import json
from pathlib import Path

from .base_tool import BaseTool

class ToolRegistry:
    """工具注册和管理系统"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """注册单个工具实例"""
        if tool.name in self._tools:
            print(f"警告: 工具 '{tool.name}' 已存在，将被覆盖")
        self._tools[tool.name] = tool
        print(f"工具 '{tool.name}' 已注册")
    
    def register_tools(self, tools: List[BaseTool]) -> None:
        """批量注册多个工具实例"""
        for tool in tools:
            self.register_tool(tool)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取指定名称的工具"""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """获取所有已注册的工具"""
        return self._tools
    
    def get_tool_schemas(self) -> List[Dict]:
        """获取所有工具的JSON Schema定义，用于LLM的function calling"""
        return [tool.get_schema() for tool in self._tools.values()]
    
    def discover_tools(self, package_path: str) -> None:
        """自动发现和注册指定包路径下的所有工具"""
        package_dir = Path(package_path)
        if not package_dir.exists() or not package_dir.is_dir():
            raise ValueError(f"无效的包路径: {package_path}")
        
        # 获取包名
        package_name = package_dir.name
        parent_package = package_dir.parent.name
        full_package = f"{parent_package}.{package_name}" if parent_package else package_name
        
        # 遍历包中的所有Python文件
        for file_path in package_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
                
            module_name = file_path.stem
            full_module_name = f"{full_package}.{module_name}"
            
            try:
                # 导入模块
                module = importlib.import_module(full_module_name)
                
                # 查找模块中的所有工具类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTool) and 
                        obj != BaseTool):
                        try:
                            # 实例化并注册工具
                            tool_instance = obj()
                            self.register_tool(tool_instance)
                        except Exception as e:
                            print(f"无法实例化工具 {name}: {e}")
                            
            except Exception as e:
                print(f"无法加载模块 {full_module_name}: {e}")
    
    def load_from_config(self, config_path: str) -> None:
        """从配置文件加载工具"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        for tool_config in config.get("tools", []):
            try:
                # 获取工具类
                module_name = tool_config.get("module")
                class_name = tool_config.get("class")
                
                if not module_name or not class_name:
                    print(f"跳过配置不完整的工具: {tool_config}")
                    continue
                
                module = importlib.import_module(module_name)
                tool_class = getattr(module, class_name)
                
                # 获取工具参数
                params = tool_config.get("params", {})
                
                # 实例化并注册工具
                tool_instance = tool_class(**params)
                self.register_tool(tool_instance)
                
            except Exception as e:
                print(f"无法加载工具 {tool_config}: {e}")
    
    def save_config(self, config_path: str) -> None:
        """将当前注册的工具保存为配置文件"""
        config = {"tools": []}
        
        for name, tool in self._tools.items():
            tool_class = tool.__class__
            module_name = tool_class.__module__
            class_name = tool_class.__name__
            
            tool_config = {
                "name": name,
                "module": module_name,
                "class": class_name,
                "params": {}  # 这里可以添加工具的初始化参数
            }
            
            config["tools"].append(tool_config)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"工具配置已保存到: {config_path}")


# 创建全局工具注册表实例
registry = ToolRegistry() 