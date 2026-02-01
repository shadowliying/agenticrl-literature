# encoding: utf-8
# 指定文件编码为UTF-8，确保中文字符能够正确处理

from queue import Queue
# 从Python标准库导入Queue类
# Queue是线程安全的队列实现，支持多线程环境下的数据传递
# 提供FIFO（先进先出）的数据结构，常用于生产者-消费者模式

class WrapperQueue():
    # 定义消息队列包装器类
    # 这个类对标准库的Queue进行了封装，提供更安全和灵活的接口
    # 主要目的是处理队列对象为None的情况，避免空指针异常
    
    def __init__(self, queue_obj:Queue = None):
        # 构造函数，初始化包装器队列
        # 参数queue_obj: Queue对象，可以是None或者标准库的Queue实例
        # 类型注解Queue表明期望传入的是Queue类型的对象
        # 默认值None允许创建不绑定具体队列的包装器实例
        #WrapperQueue()              # 没传 → queue_obj = None
        #WrapperQueue(Queue())       # 传了 → queue_obj 是一个空队列对象

        
        self.queue = queue_obj
        # 将传入的队列对象保存为实例属性
        # 如果queue_obj为None，则self.queue也为None
        # 后续的put和get操作会根据这个属性是否为None来决定是否执行实际操作
        
    def put(self, info):
        # 向队列中放入数据的方法
        # 参数info: 要放入队列的数据，可以是任意类型的对象
        # 这个方法提供了安全的数据放入功能，不会因为队列为None而报错
        
        if self.queue is not None:
            # 检查队列对象是否存在 而不是说队列是不是空的
            # 只有当队列对象不为None时才执行put操作
            # 这种设计避免了在队列未初始化时调用put方法导致的AttributeError
            
            self.queue.put(info)
            # 调用标准库Queue的put方法将数据放入队列
            # put方法是阻塞的，如果队列已满会等待直到有空间
            # info数据会被添加到队列的末尾，等待消费者获取
            
    def get(self, block=True):
        # 从队列中获取数据的方法
        # 参数block: 布尔值，控制是否阻塞等待数据
        #           True(默认): 如果队列为空会阻塞等待直到有数据
        #           False: 如果队列为空会立即抛出Empty异常
        
        ret = None
        # 初始化返回值为None
        # 如果队列对象不存在或获取失败，将返回None
        
        if self.queue is not None:
            # 检查队列对象是否存在
            # 只有当队列对象不为None时才执行get操作
            # 避免在队列未初始化时调用get方法导致的AttributeError
            
            ret = self.queue.get(block=block)
            # 调用标准库Queue的get方法从队列中获取数据
            # block参数传递给底层的get方法，控制阻塞行为
            # 返回的数据是队列中最早放入的元素（FIFO特性）
            
        return ret
        # 返回获取到的数据
        # 如果队列不存在或为空且非阻塞模式，返回None
        # 如果成功获取数据，返回队列中的实际数据对象
