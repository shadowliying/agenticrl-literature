# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

import requests
# 导入requests库，用于发送HTTP请求到远程代码执行服务

from .base_executor import BaseExecutor
# 从当前包的base_executor模块导入BaseExecutor抽象基类
# 使用相对导入，确保模块之间的正确依赖关系

from config import CODE_RUNNER_API_URL
# 从config模块导入代码执行服务的API URL配置
# 这个URL指向远程的Python代码执行服务器

class CodeExecutor(BaseExecutor):
    # 定义CodeExecutor类，继承自BaseExecutor抽象基类
    # 专门负责执行Python代码并返回执行结果

    def execute(self, code, *args, **kwargs):
        # 重写父类的抽象方法execute，实现具体的代码执行逻辑
        # 参数code: 待执行的Python代码字符串
        # *args: 可变位置参数，预留给将来的扩展
        # **kwargs: 可变关键字参数，预留给将来的扩展

        code_prefix = """import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams["axes.unicode_minus"] = False
"""
        # 定义代码前缀，在用户代码执行前自动添加
        # 第1行：导入matplotlib库，用于数据可视化
        # 第2行：导入matplotlib.pyplot模块并重命名为plt，提供绘图功能
        # 第3行：空行，提高代码可读性
        # 第4行：设置matplotlib的字体配置，使用SimHei字体支持中文显示
        #        rcParams是matplotlib的全局配置参数字典
        #        'font.sans-serif'指定无衬线字体列表，SimHei是黑体字体
        # 第5行：设置坐标轴负号显示配置为False
        #        解决matplotlib中文字体环境下负号显示为方块的问题
        #        确保负数在图表中正确显示

        url = CODE_RUNNER_API_URL
        # 将配置文件中的代码执行服务URL赋值给局部变量url
        # 这个URL指向远程的Python代码执行服务器端点

        data = {
            'id': "1111",
            'code_text': code_prefix + "\n" + code,
        }
        # 构造发送给代码执行服务的请求数据字典
        # 'id': 执行任务的唯一标识符，这里使用固定值"1111"
        #       在实际使用中可能需要生成唯一ID来追踪不同的执行任务
        # 'code_text': 完整的待执行代码，由以下部分组成：
        #              1. code_prefix: 预设的导入和配置代码
        #              2. "\n": 换行符，分隔前缀代码和用户代码
        #              3. code: 用户提供的实际Python代码

        response = requests.post(url, json=data).json()
        # 向远程代码执行服务发送POST请求并处理响应
        # requests.post(): 发送HTTP POST请求
        # url: 目标服务器地址
        # json=data: 将data字典序列化为JSON格式作为请求体发送
        #            自动设置Content-Type为application/json
        # .json(): 将响应内容解析为Python字典对象
        #          假设服务器返回的是JSON格式的响应

        return response['data']
        # 从响应字典中提取'data'字段并返回
        # 根据注释中的示例，'data'字段包含执行结果，可能包括：
        # - 文本输出：{'text': '输出内容'}
        # - 图像输出：{'img': 'base64编码的图像数据'}
        # - 多个输出项的列表形式


"""
以下是多行字符串注释，包含了详细的API使用示例和响应格式说明

```
        #### 1.输入示例
        # 展示如何构造code_text参数的完整示例
code_text = \"\"\"import matplotlib.pyplot as plt

print("hello world!")
# 输出简单的文本信息

# 示例数据
x = [1, 2, 3, 4, 5]      # X轴数据点
y = [2, 3, 5, 7, 11]     # Y轴数据点（质数序列）

# 创建图形和轴
plt.figure()             # 创建新的图形窗口

# 绘制折线图
plt.plot(x, y, marker='o', linestyle='-', color='b', label='Line Plot')
# marker='o': 数据点用圆圈标记
# linestyle='-': 使用实线连接点
# color='b': 线条颜色为蓝色
# label='Line Plot': 图例标签

# 添加标题和标签
plt.title('Simple Line Plot')  # 设置图表标题
plt.xlabel('X-axis')          # 设置X轴标签
plt.ylabel('Y-axis')          # 设置Y轴标签

# 添加图例
plt.legend()                  # 显示图例

# 显示图形
plt.show()                    # 渲染并显示图形

print("finish!")             # 输出完成信息

\"\"\"

data = {
    "id": 1111,                    # 任务ID（数字格式）
    "code_text": code_text,        # 要执行的完整代码
    "code_type":"python"           # 代码类型（虽然当前实现中未使用此字段）
}
```

#### 2.正确输出示例
# 当代码执行成功时，服务器返回的JSON响应格式
```
{
	'id': '1111',                   # 任务ID（字符串格式返回）
	'code': 200,                    # HTTP状态码，200表示成功
	'data': [                       # 执行结果数组，按输出顺序排列
		{'text': 'hello world!\n'}, # 第一个输出：print语句的文本输出
		{'img': 'iVBORw0KGgoAAAANSUhEUgAAAjMAAAHFCAYAAAAHcXhbAAAAOXRFWHRTb2Z0d2FyZQBNYXRwbG90bGliIHZlcnNpb24zLjYuMiwgaHR0cHM6Ly9tYXRwbG90bGliLm9yZy8o6BhiAAAACXBIWXMAAA9hAAAPY……(省略)ggg=='}, 
		# 第二个输出：matplotlib生成的图像，以base64编码存储
		# 完整的base64字符串被省略，实际使用中会包含完整的图像数据
		{'text': 'finish!\n'}       # 第三个输出：最后的print语句输出
		], 
    'msg': 'success',               # 执行状态消息
    'time': 0.711                   # 代码执行耗时（秒）
}
```

#### 3.错误输出示例
# 当代码执行失败时，服务器返回的错误响应格式
```
{
	'id': '1111',                   # 任务ID
	'code': 500,                    # HTTP状态码，500表示服务器内部错误
	'data': None,                   # 无执行结果数据
	'msg': 'No available kernels, please try again later.', 
	# 错误消息：没有可用的执行内核，建议稍后重试
	# 说明远程服务器的Python执行环境暂时不可用
	'time': 0.0                     # 执行耗时为0，因为实际未执行代码
}
```

"""
# 整个多行字符串提供了完整的API使用文档
# 包括输入格式、成功响应、错误响应的详细说明
# 帮助开发者理解如何正确使用CodeExecutor类