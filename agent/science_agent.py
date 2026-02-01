import json
import os
from typing import Dict, List, Any, Optional, Union, Tuple
import logging

# 导入工具调用器
from agent.tool_caller import tool_caller
from tools.scientific_tools import DataAnalysisTool, PlotGeneratorTool, StatisticalTestTool, SymbolicMathTool, MolecularWeightTool

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ScienceAgent")

class ScienceAgent:
    """科学智能体，使用大模型和科学工具解决科学问题"""
    
    def __init__(self, llm_client=None):
        """
        初始化科学智能体
        
        参数:
            llm_client: 大模型客户端，可以是OpenAI、Anthropic等
        """
        self.llm_client = llm_client
        self.tool_caller = tool_caller
        
        # 注册科学工具
        self._register_science_tools()
        
        # 系统提示词
        self.system_prompt = """
        你是一个专业的科学助手，擅长解决各种科学问题。你可以使用以下工具来辅助你的分析：
        
        1. analyze_data: 分析数据集，计算统计指标
        2. generate_plot: 生成各种科学图表
        3. statistical_test: 进行各种统计检验
        4. symbolic_math: 执行符号数学运算
        5. calculate_molecular_weight: 计算化学分子式的分子量
        
        当你需要使用这些工具时，请使用以下格式：
        
        ```json
        {
          "name": "工具名称",
          "arguments": {
            "参数1": "值1",
            "参数2": "值2"
          }
        }
        ```
        
        请根据用户的问题，选择合适的工具来解决问题。如果需要多步骤分析，可以逐步使用工具并解释每一步的结果。
        """
    
    def _register_science_tools(self):
        """注册科学工具"""
        # 实例化科学工具
        data_analysis_tool = DataAnalysisTool()
        plot_generator_tool = PlotGeneratorTool()
        statistical_test_tool = StatisticalTestTool()
        symbolic_math_tool = SymbolicMathTool()
        molecular_weight_tool = MolecularWeightTool()
        
        # 注册工具到工具注册表
        self.tool_caller.registry.register_tools([
            data_analysis_tool,
            plot_generator_tool,
            statistical_test_tool,
            symbolic_math_tool,
            molecular_weight_tool
        ])
        
        logger.info("科学工具注册完成")
    
    def get_tool_descriptions(self) -> str:
        """获取工具描述，用于提示词中"""
        tool_schemas = self.tool_caller.get_tool_schemas()
        descriptions = []
        
        for schema in tool_schemas:
            name = schema.get("name")
            description = schema.get("description")
            parameters = schema.get("parameters", {}).get("properties", {})
            
            param_desc = []
            for param_name, param_info in parameters.items():
                param_type = param_info.get("type", "any")
                param_description = param_info.get("description", "")
                required = "（必需）" if param_name in schema.get("parameters", {}).get("required", []) else "（可选）"
                param_desc.append(f"  - {param_name}: {param_type} {required} - {param_description}")
            
            tool_desc = f"- {name}: {description}\n  参数:\n" + "\n".join(param_desc)
            descriptions.append(tool_desc)
        
        return "\n\n".join(descriptions)
    
    def _parse_llm_response(self, response: str) -> Tuple[str, List[Dict]]:
        """
        从LLM响应中解析出文本内容和工具调用
        
        参数:
            response: LLM的响应文本
            
        返回:
            (文本内容, 工具调用列表)
        """
        # 这里的实现取决于您使用的LLM API
        # 以下是一个简单的示例，假设LLM返回的是JSON格式的响应
        try:
            # 尝试解析为JSON
            response_json = json.loads(response)
            text_content = response_json.get("content", "")
            tool_calls = response_json.get("tool_calls", [])
            return text_content, tool_calls
        except json.JSONDecodeError:
            # 如果不是JSON，假设是纯文本响应
            return response, []
    
    def process_query(self, query: str) -> str:
        """
        处理用户查询
        
        参数:
            query: 用户查询文本
            
        返回:
            处理结果
        """
        if not self.llm_client:
            # 如果没有LLM客户端，使用模拟的工具调用示例
            return self._mock_process_query(query)
        
        # 构建完整的提示词
        tool_descriptions = self.get_tool_descriptions()
        full_system_prompt = self.system_prompt + "\n\n可用工具详细信息:\n" + tool_descriptions
        
        # 调用LLM
        response = self.llm_client.chat(
            system=full_system_prompt,
            messages=[{"role": "user", "content": query}],
            tools=self.tool_caller.get_tool_schemas()
        )
        
        # 解析LLM响应
        text_content, tool_calls = self._parse_llm_response(response)
        
        # 执行工具调用
        if tool_calls:
            tool_results = self.tool_caller.batch_execute(tool_calls)
            
            # 将工具结果发送回LLM进行解释
            follow_up_response = self.llm_client.chat(
                system=full_system_prompt,
                messages=[
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": text_content},
                    {"role": "system", "content": f"工具执行结果: {json.dumps(tool_results, ensure_ascii=False)}"}
                ]
            )
            
            return follow_up_response
        
        return text_content
    
    def _mock_process_query(self, query: str) -> str:
        """
        模拟处理用户查询（当没有LLM客户端时使用）
        
        参数:
            query: 用户查询文本
            
        返回:
            处理结果
        """
        # 根据查询内容模拟不同的工具调用场景
        if "分析数据" in query or "统计" in query:
            # 模拟数据分析
            sample_data = [12.5, 15.3, 18.2, 10.7, 14.5, 16.8, 19.2]
            result = self.tool_caller.execute_tool("analyze_data", data=sample_data, metrics=["mean", "median", "std", "min", "max"])
            return f"数据分析结果:\n均值: {result['mean']:.2f}\n中位数: {result['median']:.2f}\n标准差: {result['std']:.2f}\n最小值: {result['min']:.2f}\n最大值: {result['max']:.2f}"
            
        elif "绘图" in query or "图表" in query:
            # 模拟绘图
            x_data = [1, 2, 3, 4, 5, 6, 7]
            y_data = [12.5, 15.3, 18.2, 10.7, 14.5, 16.8, 19.2]
            result = self.tool_caller.execute_tool(
                "generate_plot", 
                x_data=x_data, 
                y_data=y_data, 
                plot_type="line", 
                title="示例数据", 
                x_label="X轴", 
                y_label="Y轴"
            )
            return f"已生成图表，图表数据包含7个点，展示了一个上升趋势，最高点在X=7处，值为19.2"
            
        elif "方程" in query or "求导" in query or "积分" in query:
            # 模拟符号数学
            expression = "x**2 + 2*x + 1"
            result = self.tool_caller.execute_tool("symbolic_math", operation="differentiate", expression=expression)
            return f"表达式 {expression} 的导数是: {result['result']}"
            
        elif "分子量" in query or "化学" in query:
            # 模拟分子量计算
            formula = "H2O"
            result = self.tool_caller.execute_tool("calculate_molecular_weight", formula=formula)
            return f"{formula}的分子量为: {result['molecular_weight']} g/mol"
            
        elif "统计检验" in query or "假设检验" in query:
            # 模拟统计检验
            data1 = [12.5, 15.3, 18.2, 10.7, 14.5, 16.8, 19.2]
            data2 = [10.2, 12.4, 13.5, 9.8, 11.2, 14.3, 15.6]
            result = self.tool_caller.execute_tool("statistical_test", test_type="ttest_ind", data1=data1, data2=data2)
            return f"两组数据的t检验结果:\nt统计量: {result['t_statistic']:.4f}\np值: {result['p_value']:.4f}\n{'显著' if result['significant'] else '不显著'}"
            
        else:
            return "我不确定如何处理您的查询。请尝试询问关于数据分析、绘图、符号数学、分子量计算或统计检验的问题。"


# 示例用法
if __name__ == "__main__":
    # 创建科学智能体
    science_agent = ScienceAgent()
    
    # 处理用户查询
    queries = [
        "请分析这组数据: [23.5, 27.8, 22.1, 29.4, 26.7, 25.3, 24.9]",
        "请绘制一个正弦波图表",
        "计算表达式 x^3 + 3x^2 + 3x + 1 的导数",
        "计算水(H2O)和二氧化碳(CO2)的分子量",
        "进行两组数据的t检验: [67.8, 72.1, 69.5, 70.3, 71.2] 和 [65.2, 67.9, 66.4, 68.1, 67.0]"
    ]
    
    for query in queries:
        print(f"\n问题: {query}")
        print("-" * 50)
        response = science_agent.process_query(query)
        print(f"回答: {response}")
        print("=" * 80) 