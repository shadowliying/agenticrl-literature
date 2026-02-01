"""
决策树算法测试示例
这个文件演示如何使用决策树算法，并展示执行过程
"""

import math

# ========== 复制原算法的核心函数 ==========

def entropy(data):
    """计算信息熵"""
    n = len(data)
    if n == 0:
        return 0
    count0 = sum(1 for x in data if x[-1] == 0)
    count1 = n - count0
    p0 = count0 / n if count0 > 0 else 0
    p1 = count1 / n if count1 > 0 else 0
    ent = 0.0
    if p0 > 0:
        ent -= p0 * math.log2(p0)
    if p1 > 0:
        ent -= p1 * math.log2(p1)
    return ent

def information_gain(data, feature_index):
    """计算信息增益"""
    base_entropy = entropy(data)
    subset0 = [x for x in data if x[feature_index] == 0]
    subset1 = [x for x in data if x[feature_index] == 1]
    n = len(data)
    cond_entropy = (len(subset0) / n) * entropy(subset0) + (len(subset1) / n) * entropy(subset1)
    return base_entropy - cond_entropy

def build_tree(data, features):
    """构建决策树"""
    labels = [x[-1] for x in data]
    if all(l == labels[0] for l in labels):
        return labels[0]

    if not features:
        count0 = labels.count(0)
        count1 = labels.count(1)
        if count1 > count0:
            return 1
        elif count1 < count0:
            return 0
        else:
            return 0
            
    best_feature = features[0]
    best_gain = information_gain(data, best_feature)
    for f in features[1:]:
        gain = information_gain(data, f)
        if gain > best_gain or (abs(gain - best_gain) < 1e-12 and f < best_feature):
            best_gain = gain
            best_feature = f
            
    if best_gain <= 1e-12:
        count0 = labels.count(0)
        count1 = labels.count(1)
        if count1 > count0:
            return 1
        elif count1 < count0:
            return 0
        else:
            return 0

    subset0 = [x for x in data if x[best_feature] == 0]
    subset1 = [x for x in data if x[best_feature] == 1]
    remaining_features = [f for f in features if f != best_feature]

    left_tree = build_tree(subset0, remaining_features) if subset0 else 0
    right_tree = build_tree(subset1, remaining_features) if subset1 else 0
    return (best_feature, left_tree, right_tree)

def predict(tree, sample):
    """预测"""
    if isinstance(tree, int):
        return tree
    feature_index, left_tree, right_tree = tree
    if sample[feature_index] == 0:
        return predict(left_tree, sample)
    else:
        return predict(right_tree, sample)


# ========== 辅助函数：可视化决策树 ==========

def print_tree(tree, feature_names=None, indent="", is_left=True):
    """
    打印决策树的结构
    """
    if isinstance(tree, int):
        print(f"{indent}└─ 预测: {'通过' if tree == 1 else '不通过'} ({tree})")
        return
    
    feature_index, left_tree, right_tree = tree
    
    if feature_names:
        feature_name = feature_names[feature_index]
    else:
        feature_name = f"特征{feature_index}"
    
    print(f"{indent}{feature_name}?")
    
    # 打印左子树（值为0）
    print(f"{indent}├─ 否(0):")
    print_tree(left_tree, feature_names, indent + "│  ", True)
    
    # 打印右子树（值为1）
    print(f"{indent}└─ 是(1):")
    print_tree(right_tree, feature_names, indent + "   ", False)


# ========== 示例1：学生考试预测 ==========

print("=" * 60)
print("示例1：预测学生是否通过考试")
print("=" * 60)

# 训练数据
# 特征0: 是否完成作业 (0=否, 1=是)
# 特征1: 是否认真听课 (0=否, 1=是)
# 标签: 是否通过考试 (0=不通过, 1=通过)
train_data_1 = [
    [1, 1, 1],  # 完成作业，认真听课 → 通过
    [1, 0, 0],  # 完成作业，不认真听课 → 不通过
    [0, 1, 0],  # 不完成作业，认真听课 → 不通过
    [0, 0, 0],  # 不完成作业，不认真听课 → 不通过
]

print("\n📊 训练数据：")
print("样本 | 完成作业 | 认真听课 | 结果")
print("-" * 40)
for i, data in enumerate(train_data_1, 1):
    print(f"  {i}  |    {data[0]}    |    {data[1]}    | {'通过' if data[2] == 1 else '不通过'}")

# 计算原始熵
original_entropy = entropy(train_data_1)
print(f"\n📈 原始数据的信息熵: {original_entropy:.4f}")

# 计算每个特征的信息增益
print("\n📊 各特征的信息增益：")
for i in range(2):
    gain = information_gain(train_data_1, i)
    feature_name = "完成作业" if i == 0 else "认真听课"
    print(f"  特征{i}（{feature_name}）: {gain:.4f}")

# 构建决策树
features_1 = [0, 1]
tree_1 = build_tree(train_data_1, features_1)

print("\n🌳 构建的决策树结构：")
print(f"决策树: {tree_1}")
print("\n决策树可视化：")
print_tree(tree_1, ["完成作业", "认真听课"])

# 预测新数据
test_data_1 = [
    [1, 1],  # 完成作业，认真听课
    [0, 1],  # 不完成作业，认真听课
    [1, 0],  # 完成作业，不认真听课
    [0, 0],  # 不完成作业，不认真听课
]

print("\n🔮 预测结果：")
print("完成作业 | 认真听课 | 预测结果")
print("-" * 40)
for sample in test_data_1:
    result = predict(tree_1, sample)
    print(f"   {sample[0]}    |    {sample[1]}    | {'通过' if result == 1 else '不通过'} ({result})")


# ========== 示例2：天气与出游决策 ==========

print("\n\n" + "=" * 60)
print("示例2：预测是否适合出去玩")
print("=" * 60)

# 训练数据
# 特征0: 天气是否好 (0=否, 1=是)
# 特征1: 是否有空闲时间 (0=否, 1=是)
# 特征2: 是否有钱 (0=否, 1=是)
# 标签: 是否出去玩 (0=不去, 1=去)
train_data_2 = [
    [1, 1, 1, 1],  # 天气好，有时间，有钱 → 去
    [1, 1, 0, 1],  # 天气好，有时间，没钱 → 去
    [1, 0, 1, 0],  # 天气好，没时间，有钱 → 不去
    [1, 0, 0, 0],  # 天气好，没时间，没钱 → 不去
    [0, 1, 1, 0],  # 天气差，有时间，有钱 → 不去
    [0, 1, 0, 0],  # 天气差，有时间，没钱 → 不去
    [0, 0, 1, 0],  # 天气差，没时间，有钱 → 不去
    [0, 0, 0, 0],  # 天气差，没时间，没钱 → 不去
]

print("\n📊 训练数据：")
print("样本 | 天气好 | 有时间 | 有钱 | 决定")
print("-" * 50)
for i, data in enumerate(train_data_2, 1):
    print(f"  {i}  |   {data[0]}   |   {data[1]}   |  {data[2]}  | {'去玩' if data[3] == 1 else '不去'}")

# 计算原始熵
original_entropy_2 = entropy(train_data_2)
print(f"\n📈 原始数据的信息熵: {original_entropy_2:.4f}")

# 计算每个特征的信息增益
print("\n📊 各特征的信息增益：")
feature_names_2 = ["天气好", "有时间", "有钱"]
for i in range(3):
    gain = information_gain(train_data_2, i)
    print(f"  特征{i}（{feature_names_2[i]}）: {gain:.4f}")

# 构建决策树
features_2 = [0, 1, 2]
tree_2 = build_tree(train_data_2, features_2)

print("\n🌳 构建的决策树结构：")
print(f"决策树: {tree_2}")
print("\n决策树可视化：")
print_tree(tree_2, feature_names_2)

# 预测新数据
test_data_2 = [
    [1, 1, 1],  # 天气好，有时间，有钱
    [1, 1, 0],  # 天气好，有时间，没钱
    [0, 1, 1],  # 天气差，有时间，有钱
    [1, 0, 1],  # 天气好，没时间，有钱
]

print("\n🔮 预测结果：")
print("天气好 | 有时间 | 有钱 | 预测结果")
print("-" * 45)
for sample in test_data_2:
    result = predict(tree_2, sample)
    print(f"  {sample[0]}   |   {sample[1]}   |  {sample[2]}  | {'去玩' if result == 1 else '不去'} ({result})")


print("\n\n" + "=" * 60)
print("🎉 测试完成！")
print("=" * 60)
print("\n💡 关键要点：")
print("1. 信息熵衡量数据的混乱程度（0=纯净，1=最混乱）")
print("2. 信息增益帮助选择最重要的特征")
print("3. 决策树通过递归分割数据来构建")
print("4. 预测时沿着树的路径走到叶子节点")

