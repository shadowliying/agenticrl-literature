# encoding: utf-8
# 配置模块初始化文件
# 该文件的作用是将config.py中的所有配置变量导入到config包的命名空间中
# 使得其他模块可以通过 "from config import VARIABLE_NAME" 的方式直接导入配置项

from .config import *
# 导入config.py模块中的所有公共变量和常量
# 包括：语言配置、LLM配置、搜索引擎配置、API密钥等
# 这种导入方式使得配置项可以在整个项目中被方便地访问