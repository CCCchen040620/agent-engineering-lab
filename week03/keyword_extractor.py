def extract_keyword(question):
    known_keywords = [
        "差旅报销",
        "主管审批",
        "远程办公",
        "安全培训",
        "股票期权",
        "弹性工作制",
        "报销",
        "请假",
        "加班",
        "年假",
        "病假",
    ]

    for keyword in known_keywords:
        if keyword in question:
            return keyword

    return question