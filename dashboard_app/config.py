# config.py

# 第一种排序规则
SORT_ORDER_1 = [
    "query",
    "Generated query based on history",
    "RAG Type Decision Prompt",
    "User input language detected",
    "Obtain the category and category prompt words based on the question.",
    "Problem Analysis",
    "Generation of similar problems",
    "result_input_vectors",
    "knowledge openarch",
    "knowledge milvus",
    "knowledge sorted",
    "jira openarch Database query",
    "jira milvus Database query",
    "jira sorted",
    "Knowledge base response"
]

# 第二种排序规则 (用于补充或备用)
SORT_ORDER_2 = [
    "query",
    "Generated query based on history",
    "RAG Type Decision Prompt",
    "User input language detected",
    "Obtain the category and category prompt words based on the question.",
    "Problem Analysis",
    "Generation of similar problems",
    "result_input_vectors",
    "jira openarch Database query",
    "jira milvus Database query",
    "retrieval_jira_top_k"
]

# 合并成一个用于查找索引的映射表，优先使用列表1，列表2补充
# 这样我们可以给每个 Features 赋予一个排序权重
SORT_MAPPING = {k: i for i, k in enumerate(SORT_ORDER_1)}
current_max = len(SORT_ORDER_1)
for item in SORT_ORDER_2:
    if item not in SORT_MAPPING:
        SORT_MAPPING[item] = current_max
        current_max += 1