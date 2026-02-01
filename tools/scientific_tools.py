import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from scipy import stats
import sympy as sp

from .base_tool import BaseTool

class DataAnalysisTool(BaseTool):
    """数据分析工具"""
    
    def __init__(self):
        super().__init__(
            name="analyze_data",
            description="分析数据集，计算统计指标如均值、中位数、标准差等"
        )
    
    def _run(self, data: List[float], metrics: List[str] = ["mean", "median", "std"]) -> Dict[str, float]:
        """
        分析数据并返回指定的统计指标
        
        参数:
            data: 要分析的数值数据列表
            metrics: 要计算的统计指标列表
            
        返回:
            包含各统计指标的字典
        """
        results = {}
        data_array = np.array(data)
        
        for metric in metrics:
            if metric == "mean":
                results["mean"] = float(np.mean(data_array))
            elif metric == "median":
                results["median"] = float(np.median(data_array))
            elif metric == "std":
                results["std"] = float(np.std(data_array))
            elif metric == "min":
                results["min"] = float(np.min(data_array))
            elif metric == "max":
                results["max"] = float(np.max(data_array))
            elif metric == "q1":
                results["q1"] = float(np.percentile(data_array, 25))
            elif metric == "q3":
                results["q3"] = float(np.percentile(data_array, 75))
        
        return results
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "要分析的数值数据列表",
                        "items": {"type": "number"}
                    },
                    "metrics": {
                        "type": "array",
                        "description": "要计算的统计指标列表，可选值：mean, median, std, min, max, q1, q3",
                        "items": {"type": "string", "enum": ["mean", "median", "std", "min", "max", "q1", "q3"]},
                        "default": ["mean", "median", "std"]
                    }
                },
                "required": ["data"]
            }
        }


class PlotGeneratorTool(BaseTool):
    """科学绘图工具"""
    
    def __init__(self):
        super().__init__(
            name="generate_plot",
            description="生成各种科学图表，如散点图、折线图、柱状图等"
        )
    
    def _run(self, 
             x_data: List[float], 
             y_data: List[float], 
             plot_type: str = "line", 
             title: str = "",
             x_label: str = "", 
             y_label: str = "",
             color: str = "blue") -> Dict[str, str]:
        """
        生成科学图表并返回base64编码的图像
        
        参数:
            x_data: X轴数据
            y_data: Y轴数据
            plot_type: 图表类型，可选值：line, scatter, bar, histogram
            title: 图表标题
            x_label: X轴标签
            y_label: Y轴标签
            color: 图表颜色
            
        返回:
            包含base64编码图像的字典
        """
        plt.figure(figsize=(10, 6))
        
        if plot_type == "line":
            plt.plot(x_data, y_data, color=color)
        elif plot_type == "scatter":
            plt.scatter(x_data, y_data, color=color)
        elif plot_type == "bar":
            plt.bar(x_data, y_data, color=color)
        elif plot_type == "histogram":
            plt.hist(y_data, bins=10, color=color)
        
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 保存图像为base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return {"image": image_base64}
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "x_data": {
                        "type": "array",
                        "description": "X轴数据",
                        "items": {"type": "number"}
                    },
                    "y_data": {
                        "type": "array",
                        "description": "Y轴数据",
                        "items": {"type": "number"}
                    },
                    "plot_type": {
                        "type": "string",
                        "description": "图表类型",
                        "enum": ["line", "scatter", "bar", "histogram"],
                        "default": "line"
                    },
                    "title": {
                        "type": "string",
                        "description": "图表标题",
                        "default": ""
                    },
                    "x_label": {
                        "type": "string",
                        "description": "X轴标签",
                        "default": ""
                    },
                    "y_label": {
                        "type": "string",
                        "description": "Y轴标签",
                        "default": ""
                    },
                    "color": {
                        "type": "string",
                        "description": "图表颜色",
                        "default": "blue"
                    }
                },
                "required": ["x_data", "y_data"]
            }
        }


class StatisticalTestTool(BaseTool):
    """统计检验工具"""
    
    def __init__(self):
        super().__init__(
            name="statistical_test",
            description="进行各种统计检验，如t检验、卡方检验等"
        )
    
    def _run(self, 
             test_type: str,
             data1: List[float],
             data2: Optional[List[float]] = None,
             alpha: float = 0.05) -> Dict[str, Any]:
        """
        执行统计检验
        
        参数:
            test_type: 检验类型，可选值：ttest_ind, ttest_1samp, chi2_contingency
            data1: 第一组数据
            data2: 第二组数据（对于某些检验类型是必需的）
            alpha: 显著性水平
            
        返回:
            包含检验结果的字典
        """
        results = {}
        
        if test_type == "ttest_ind" and data2 is not None:
            # 独立样本t检验
            t_stat, p_value = stats.ttest_ind(data1, data2)
            results = {
                "test_type": "独立样本t检验",
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant": p_value < alpha,
                "alpha": alpha
            }
        
        elif test_type == "ttest_1samp":
            # 单样本t检验
            population_mean = 0
            if data2 and len(data2) == 1:
                population_mean = data2[0]
            t_stat, p_value = stats.ttest_1samp(data1, population_mean)
            results = {
                "test_type": "单样本t检验",
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant": p_value < alpha,
                "alpha": alpha,
                "population_mean": population_mean
            }
            
        elif test_type == "chi2_contingency" and data2 is not None:
            # 将data1和data2转换为列联表
            if len(data1) == len(data2):
                contingency_table = np.array([data1, data2])
                chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
                results = {
                    "test_type": "卡方独立性检验",
                    "chi2_statistic": float(chi2),
                    "p_value": float(p_value),
                    "degrees_of_freedom": int(dof),
                    "significant": p_value < alpha,
                    "alpha": alpha
                }
        
        return results
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "test_type": {
                        "type": "string",
                        "description": "统计检验类型",
                        "enum": ["ttest_ind", "ttest_1samp", "chi2_contingency"]
                    },
                    "data1": {
                        "type": "array",
                        "description": "第一组数据",
                        "items": {"type": "number"}
                    },
                    "data2": {
                        "type": "array",
                        "description": "第二组数据（对于某些检验类型是必需的）",
                        "items": {"type": "number"}
                    },
                    "alpha": {
                        "type": "number",
                        "description": "显著性水平",
                        "default": 0.05
                    }
                },
                "required": ["test_type", "data1"]
            }
        }


class SymbolicMathTool(BaseTool):
    """符号数学计算工具"""
    
    def __init__(self):
        super().__init__(
            name="symbolic_math",
            description="执行符号数学运算，如求导、积分、方程求解等"
        )
    
    def _run(self, 
             operation: str,
             expression: str,
             variable: str = "x",
             **kwargs) -> Dict[str, Any]:
        """
        执行符号数学运算
        
        参数:
            operation: 运算类型，可选值：differentiate, integrate, solve, simplify, expand
            expression: 数学表达式字符串
            variable: 变量名
            **kwargs: 其他特定于操作的参数
            
        返回:
            包含运算结果的字典
        """
        results = {}
        
        try:
            # 解析表达式
            expr = sp.sympify(expression)
            var = sp.Symbol(variable)
            
            if operation == "differentiate":
                # 求导
                order = kwargs.get("order", 1)
                result = sp.diff(expr, var, order)
                results = {
                    "operation": "求导",
                    "original_expression": str(expr),
                    "result": str(result),
                    "latex": sp.latex(result)
                }
                
            elif operation == "integrate":
                # 积分
                definite = kwargs.get("definite", False)
                if definite:
                    lower = kwargs.get("lower", 0)
                    upper = kwargs.get("upper", 1)
                    result = sp.integrate(expr, (var, lower, upper))
                    results = {
                        "operation": "定积分",
                        "original_expression": str(expr),
                        "lower_bound": lower,
                        "upper_bound": upper,
                        "result": str(result),
                        "latex": sp.latex(result)
                    }
                else:
                    result = sp.integrate(expr, var)
                    results = {
                        "operation": "不定积分",
                        "original_expression": str(expr),
                        "result": str(result),
                        "latex": sp.latex(result)
                    }
                    
            elif operation == "solve":
                # 方程求解
                result = sp.solve(expr, var)
                results = {
                    "operation": "方程求解",
                    "equation": str(expr) + " = 0",
                    "solutions": [str(sol) for sol in result],
                    "latex": sp.latex(result)
                }
                
            elif operation == "simplify":
                # 表达式化简
                result = sp.simplify(expr)
                results = {
                    "operation": "表达式化简",
                    "original_expression": str(expr),
                    "result": str(result),
                    "latex": sp.latex(result)
                }
                
            elif operation == "expand":
                # 表达式展开
                result = sp.expand(expr)
                results = {
                    "operation": "表达式展开",
                    "original_expression": str(expr),
                    "result": str(result),
                    "latex": sp.latex(result)
                }
                
        except Exception as e:
            results = {"error": str(e)}
            
        return results
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "数学运算类型",
                        "enum": ["differentiate", "integrate", "solve", "simplify", "expand"]
                    },
                    "expression": {
                        "type": "string",
                        "description": "数学表达式字符串，例如 'x**2 + 2*x + 1'"
                    },
                    "variable": {
                        "type": "string",
                        "description": "变量名",
                        "default": "x"
                    },
                    "order": {
                        "type": "integer",
                        "description": "求导阶数（仅用于求导）",
                        "default": 1
                    },
                    "definite": {
                        "type": "boolean",
                        "description": "是否计算定积分（仅用于积分）",
                        "default": False
                    },
                    "lower": {
                        "type": "number",
                        "description": "定积分下限（仅用于定积分）",
                        "default": 0
                    },
                    "upper": {
                        "type": "number",
                        "description": "定积分上限（仅用于定积分）",
                        "default": 1
                    }
                },
                "required": ["operation", "expression"]
            }
        }


class MolecularWeightTool(BaseTool):
    """分子量计算工具"""
    
    def __init__(self):
        super().__init__(
            name="calculate_molecular_weight",
            description="计算化学分子式的分子量"
        )
        # 定义常见元素的原子量
        self.atomic_weights = {
            'H': 1.008, 'He': 4.003, 'Li': 6.941, 'Be': 9.012,
            'B': 10.811, 'C': 12.011, 'N': 14.007, 'O': 15.999,
            'F': 18.998, 'Ne': 20.180, 'Na': 22.990, 'Mg': 24.305,
            'Al': 26.982, 'Si': 28.086, 'P': 30.974, 'S': 32.065,
            'Cl': 35.453, 'Ar': 39.948, 'K': 39.098, 'Ca': 40.078,
            'Fe': 55.845, 'Cu': 63.546, 'Zn': 65.38
        }
    
    def _parse_formula(self, formula: str) -> Dict[str, int]:
        """解析化学分子式，返回元素及其原子数的字典"""
        import re
        
        # 正则表达式匹配元素符号和数量
        pattern = r'([A-Z][a-z]*)(\d*)'
        matches = re.findall(pattern, formula)
        
        elements = {}
        for element, count in matches:
            if element in self.atomic_weights:
                count = int(count) if count else 1
                elements[element] = elements.get(element, 0) + count
        
        return elements
    
    def _run(self, formula: str) -> Dict[str, Any]:
        """
        计算化学分子式的分子量
        
        参数:
            formula: 化学分子式，如 'H2O', 'C6H12O6'
            
        返回:
            包含分子量和元素组成的字典
        """
        try:
            elements = self._parse_formula(formula)
            
            if not elements:
                return {"error": "无法解析分子式或包含未知元素"}
            
            # 计算分子量
            molecular_weight = 0
            composition = {}
            
            for element, count in elements.items():
                element_weight = self.atomic_weights[element] * count
                molecular_weight += element_weight
                composition[element] = {
                    "count": count,
                    "atomic_weight": self.atomic_weights[element],
                    "total_weight": element_weight
                }
            
            return {
                "formula": formula,
                "molecular_weight": round(molecular_weight, 4),
                "composition": composition
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "formula": {
                        "type": "string",
                        "description": "化学分子式，如 'H2O', 'C6H12O6'"
                    }
                },
                "required": ["formula"]
            }
        } 