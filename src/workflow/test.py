def merge_intervals(intervals):
    """
    合并重叠区间的函数。
    
    算法思路：
    1. 首先按照每个区间的起始点对区间列表进行排序，这样可以保证重叠区间是连续的。
    2. 初始化一个结果数组merged，用于存储合并后的不重叠区间。
    3. 遍历排序后的区间列表：
    - 如果结果数组为空，或者当前区间的起始点大于结果数组最后一个区间的结束点，则直接添加当前区间（表示无重叠）。
    - 否则，将当前区间与结果数组最后一个区间合并，更新结束点为两者结束点的最大值（表示重叠区间合并）。
    4. 最终返回合并后的结果数组。
    
    时间复杂度：O(n log n)，主要耗时在排序上，合并过程为O(n)。
    空间复杂度：O(n)，用于存储合并后的结果。
    """

    # 首先按照每个区间的起始点排序，确保重叠区间连续
    intervals.sort(key=lambda x: x[0])

    merged = []  # 存储合并后的区间

    for interval in intervals:
        if not merged or merged[-1][1] < interval[0]:
            # 如果结果数组为空，或者当前区间与最后一个区间不重叠，则添加当前区间
            merged.append(interval)
        else:
            # 否则，合并当前区间与最后一个区间，更新结束点为最大值
            merged[-1][1] = max(merged[-1][1], interval[1])

    return merged

# 示例输入
intervals = [[1, 3], [2, 6], [8, 10], [15, 18]]
# 调用函数
result = merge_intervals(intervals)
# 输出结果
print(result)  # [[1, 6], [8, 10], [15, 18]]