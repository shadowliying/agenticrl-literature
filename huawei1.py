"""
决策树算法 - ID3算法实现
用于根据训练数据构建决策树，并对新数据进行分类预测

什么是决策树？
决策树就像一个"20个问题"游戏，通过问一系列是/否的问题来做出决定。
例如：判断是否适合出去玩
- 天气好吗？
  - 是 → 有时间吗？
    - 是 → 去玩！
    - 否 → 不去
  - 否 → 不去
"""

import sys  # 用于读取标准输入
import math  # 用于数学计算，特别是对数运算


def entropy(data):
    """
    计算信息熵 - 用来衡量数据的混乱程度
    
    什么是熵？
    熵就是数据的"混乱度"：
    - 如果所有数据都是同一类别（全是0或全是1），熵 = 0（非常有序）
    - 如果数据一半0一半1，熵 = 1（最混乱）
    
    例子：
    数据1: [0, 0, 0, 0] → 熵 = 0（完全纯净）
    数据2: [0, 1, 0, 1] → 熵 = 1（最混乱）
    数据3: [0, 0, 0, 1] → 熵 = 0.81（有点混乱）
    
    参数:
        data: 训练数据列表，每条数据的最后一个元素是标签（0或1）
    返回:
        熵值（0到1之间的浮点数）
    """
    n = len(data)  # 数据总数
    if n == 0:  # 如果没有数据
        return 0  # 返回熵为0
    
    # 统计标签为0的数据个数
    # x[-1] 表示取每条数据的最后一个元素（标签）
    count0 = sum(1 for x in data if x[-1] == 0)
    
    # 标签为1的数据个数 = 总数 - 标签为0的个数
    count1 = n - count0
    
    # 计算标签为0的概率
    p0 = count0 / n if count0 > 0 else 0
    
    # 计算标签为1的概率
    p1 = count1 / n if count1 > 0 else 0
    
    # 初始化熵值
    ent = 0.0
    
    # 熵的计算公式: Entropy = -p0*log2(p0) - p1*log2(p1)
    # 如果p0大于0，累加 -p0*log2(p0)
    if p0 > 0:
        ent -= p0 * math.log2(p0)
    
    # 如果p1大于0，累加 -p1*log2(p1)
    if p1 > 0:
        ent -= p1 * math.log2(p1)
    
    return ent  # 返回计算出的熵值


def information_gain(data, feature_index):
    """
    计算信息增益 - 用来判断某个特征对分类的重要程度
    
    什么是信息增益？
    信息增益 = 使用这个特征前的混乱度 - 使用这个特征后的混乱度
    信息增益越大，说明这个特征越重要，越能帮助我们做出正确的分类。
    
    例子：假设我们要判断是否出去玩
    特征1: 天气（好/坏）
    特征2: 今天是星期几
    
    如果"天气"能让我们更确定要不要出去玩，那么"天气"的信息增益就大。
    
    参数:
        data: 训练数据
        feature_index: 要计算的特征的索引位置
    返回:
        该特征的信息增益值
    """
    # 计算使用这个特征之前的熵（原始混乱度）
    base_entropy = entropy(data)
    
    # 将数据按照这个特征的值分成两组
    # subset0: 该特征值为0的所有数据
    subset0 = [x for x in data if x[feature_index] == 0]
    
    # subset1: 该特征值为1的所有数据
    subset1 = [x for x in data if x[feature_index] == 1]
    
    n = len(data)  # 数据总数
    
    # 计算使用这个特征之后的条件熵（加权平均的混乱度）
    # 条件熵 = (subset0的比例 × subset0的熵) + (subset1的比例 × subset1的熵)
    cond_entropy = (len(subset0) / n) * entropy(subset0) + (len(subset1) / n) * entropy(subset1)
    
    # 信息增益 = 原始熵 - 条件熵
    return base_entropy - cond_entropy


def build_tree(data, features):
    """
    递归构建决策树
    
    决策树的构建过程就像玩"猜猜看"游戏：
    1. 选择最有用的问题（信息增益最大的特征）
    2. 根据答案把数据分成两组
    3. 对每一组重复这个过程
    4. 直到所有数据都是同一类别，或者没有问题可问了
    
    例子：
    数据: [(天气好, 有时间, 去玩), (天气好, 没时间, 不去), (天气差, 有时间, 不去)]
    
    步骤1: 选"天气"这个特征（假设它信息增益最大）
    步骤2: 分成两组
      - 天气好的数据 → 继续判断"时间"
      - 天气差的数据 → 直接判定"不去"
    
    参数:
        data: 当前要处理的训练数据
        features: 还可以使用的特征列表
    返回:
        决策树（可能是一个整数标签，或者是一个元组）
    """
    
    # 提取所有数据的标签（最后一列）
    labels = [x[-1] for x in data]
    
    # 停止条件1: 如果所有数据的标签都相同
    # 例如: [0, 0, 0] 或 [1, 1, 1]
    if all(l == labels[0] for l in labels):
        return labels[0]  # 返回这个标签作为叶子节点

    # 停止条件2: 如果没有特征可以用了
    if not features:
        # 统计标签为0和1的个数
        count0 = labels.count(0)
        count1 = labels.count(1)
        
        # 返回数量更多的那个标签（多数投票）
        if count1 > count0:
            return 1
        elif count1 < count0:
            return 0
        else:  # 如果数量相同，返回0
            return 0
    
    # 选择最佳特征：从第一个特征开始
    best_feature = features[0]
    best_gain = information_gain(data, best_feature)
    
    # 遍历所有剩余特征，找出信息增益最大的那个
    for f in features[1:]:
        gain = information_gain(data, f)
        
        # 如果当前特征的信息增益更大，或者信息增益相同但特征索引更小
        # （这样可以保证结果的一致性）
        if gain > best_gain or (abs(gain - best_gain) < 1e-12 and f < best_feature):
            best_gain = gain
            best_feature = f
    
    # 如果最佳信息增益太小（几乎为0），说明剩余特征都没用了
    if best_gain <= 1e-12:
        count0 = labels.count(0)
        count1 = labels.count(1)
        
        # 进行多数投票
        if count1 > count0:
            return 1
        elif count1 < count0:
            return 0
        else:
            return 0

    # 根据最佳特征的值，将数据分成两组
    # subset0: 最佳特征值为0的所有数据
    subset0 = [x for x in data if x[best_feature] == 0]
    
    # subset1: 最佳特征值为1的所有数据
    subset1 = [x for x in data if x[best_feature] == 1]
    
    # 从特征列表中移除已使用的特征
    remaining_features = [f for f in features if f != best_feature]

    # 递归构建左子树（特征值为0的分支）
    # 如果subset0为空，返回默认值0
    left_tree = build_tree(subset0, remaining_features) if subset0 else 0
    
    # 递归构建右子树（特征值为1的分支）
    # 如果subset1为空，返回默认值0
    right_tree = build_tree(subset1, remaining_features) if subset1 else 0
    
    # 返回一个元组：(特征索引, 左子树, 右子树)
    return (best_feature, left_tree, right_tree)


def predict(tree, sample):
    """
    使用构建好的决策树对新样本进行预测
    
    预测过程就像沿着树走下去：
    1. 看当前节点问的是什么问题（哪个特征）
    2. 根据样本在这个特征上的值（0或1），选择走左边还是右边
    3. 继续往下走，直到走到叶子节点
    4. 叶子节点的值就是预测结果
    
    例子：
    决策树: (特征0, (特征1, 0, 1), 0)
    样本: [1, 1]
    
    步骤1: 看特征0，样本值为1，走右边 → 到达叶子节点0
    预测结果: 0
    
    参数:
        tree: 决策树（整数或元组）
        sample: 要预测的样本数据
    返回:
        预测的标签（0或1）
    """
    # 如果树是一个整数，说明到达了叶子节点
    if isinstance(tree, int):
        return tree  # 直接返回这个整数作为预测结果
    
    # 否则，树是一个元组 (特征索引, 左子树, 右子树)
    feature_index, left_tree, right_tree = tree
    
    # 查看样本在这个特征上的值
    if sample[feature_index] == 0:
        # 如果特征值为0，递归预测左子树
        return predict(left_tree, sample)
    else:
        # 如果特征值为1，递归预测右子树
        return predict(right_tree, sample)


# ==================== 主程序 ====================

# 从标准输入读取所有数据并分割成单词列表
data = sys.stdin.read().strip().split()

ptr = 0  # 指针，用于遍历输入数据

# 读取训练样本数量 n
n = int(data[ptr])
ptr += 1

# 读取特征数量 m
m = int(data[ptr])
ptr += 1

# 存储训练数据的列表
train_data = []

# 读取 n 条训练数据
for _ in range(n):
    # 读取 m 个特征值
    features = list(map(int, data[ptr:ptr + m]))
    ptr += m
    
    # 读取标签（0或1）
    label = int(data[ptr])
    ptr += 1
    
    # 将特征和标签组合成一条完整的数据，添加到训练集中
    # 例如: features=[1,0,1], label=1 → [1,0,1,1]
    train_data.append(features + [label])

# 读取查询数量 q
q = int(data[ptr])
ptr += 1

# 存储查询数据的列表
query_data = []

# 读取 q 条查询数据
for _ in range(q):
    # 每条查询数据有 m 个特征值（没有标签）
    query_data.append(list(map(int, data[ptr:ptr + m])))
    ptr += m

# 创建特征索引列表 [0, 1, 2, ..., m-1]
features_list = list(range(m))

# 使用训练数据构建决策树
tree = build_tree(train_data, features_list)

# 对每条查询数据进行预测并输出结果
for sample in query_data:
    print(predict(tree, sample))