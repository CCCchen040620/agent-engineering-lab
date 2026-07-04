def extract_keyword(question):
    known_keywords = ["安全培训", "报销", "请假", "年假", "病假", "弹性工作制"]

    for keyword in known_keywords:
        if keyword in question:
            return keyword

    return question