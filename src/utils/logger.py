# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

import logging
# 导入Python标准库中的logging模块
# logging模块提供了灵活的日志记录功能，支持不同级别的日志输出

from logging import handlers
# 从logging模块导入handlers子模块
# handlers模块包含各种日志处理器，如文件处理器、轮转处理器等
# 这里主要使用TimedRotatingFileHandler实现按时间轮转的日志文件

import os
# 导入os模块，用于操作系统相关的功能
# 主要用于文件路径操作和目录创建

LOG_TOES_PATH = "./logs/running_logs.log"
# 定义日志文件的存储路径
# 使用相对路径，在项目根目录下创建logs文件夹
# running_logs.log是主要的运行日志文件名
# 这个路径将用于存储系统的运行状态和调试信息

os.makedirs(os.path.dirname(LOG_TOES_PATH), exist_ok=True)
# 创建日志文件所在的目录
# os.path.dirname(LOG_TOES_PATH): 获取日志文件路径的目录部分，即"./logs"
# os.makedirs(): 递归创建目录，如果父目录不存在也会一并创建
# exist_ok=True: 如果目录已存在则不报错，避免重复创建时的异常

time_rota_handler = handlers.TimedRotatingFileHandler(
    filename=LOG_TOES_PATH,
    when="w0",
    interval=4,
    backupCount=12,
    encoding="utf-8")
# 创建基于时间轮转的文件处理器
# filename=LOG_TOES_PATH: 指定日志文件的路径
# when="w0": 设置轮转时间单位，"w0"表示每周一（Monday=0）进行轮转
#           其他选项："S"(秒)、"M"(分)、"H"(小时)、"D"(天)、"W0-W6"(周几)
# interval=4: 轮转间隔，结合when="w0"表示每4周轮转一次（约1个月）
# backupCount=12: 保留的备份文件数量，超过12个备份文件时会删除最旧的
#                这样可以保留大约12个月的日志历史记录
# encoding="utf-8": 指定日志文件的编码格式，确保中文内容正确写入

time_rota_handler.setFormatter(
    logging.Formatter(
        fmt = '%(message)s'
    )
)
# 为日志处理器设置格式化器
# logging.Formatter(): 创建日志格式化器对象
# fmt='%(message)s': 设置日志输出格式，只输出消息内容本身
#                   不包含时间戳、日志级别、模块名等额外信息
#                   这种简洁格式适合记录纯净的状态信息
# 其他常用格式字段：%(asctime)s(时间)、%(levelname)s(级别)、%(name)s(记录器名称)

model_logger = logging.Logger(name="查看当前状态", level=logging.DEBUG)
# 创建自定义的日志记录器实例
# name="查看当前状态": 设置记录器的名称，用于标识不同的日志记录器
#                    这个中文名称表明主要用于记录系统当前状态信息
# level=logging.DEBUG: 设置日志级别为DEBUG，这是最低的日志级别
#                      会记录所有级别的日志：DEBUG、INFO、WARNING、ERROR、CRITICAL
#                      DEBUG级别适合开发和调试阶段，记录详细的运行信息

model_logger.addHandler(time_rota_handler)
# 将时间轮转文件处理器添加到日志记录器中
# 这样model_logger记录的所有日志都会通过time_rota_handler写入到文件
# 支持按时间自动轮转和备份，避免单个日志文件过大
# 日志记录器可以添加多个处理器，同时输出到文件、控制台等不同目标