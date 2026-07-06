from week03.keyword_extractor import extract_keyword


def test_extract_keyword_finds_reimbursement():
    keyword = extract_keyword("普通报销需要什么材料？")

    assert keyword == "报销"


def test_extract_keyword_finds_safety_training():
    keyword = extract_keyword("新员工什么时候完成安全培训？")

    assert keyword == "安全培训"


def test_extract_keyword_returns_original_question_when_unknown():
    keyword = extract_keyword("公司有没有健身房？")

    assert keyword == "公司有没有健身房？"


def test_extract_keyword_prefers_more_specific_keyword():
    keyword = extract_keyword("差旅报销多久内提交？")

    assert keyword == "差旅报销"


def test_extract_keyword_finds_remote_work():
    keyword = extract_keyword("员工可以远程办公吗？")

    assert keyword == "远程办公"


def test_extract_keyword_finds_overtime():
    keyword = extract_keyword("加班需要怎么申请？")

    assert keyword == "加班"


def test_extract_keyword_finds_manager_approval():
    keyword = extract_keyword("主管审批后什么时候生效？")

    assert keyword == "主管审批"


def test_extract_keyword_finds_stock_option():
    keyword = extract_keyword("公司有没有股票期权？")

    assert keyword == "股票期权"