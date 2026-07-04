from week01.study_planner import calculate_total_hours


def test_calculate_total_hours_for_20_weeks():
    result = calculate_total_hours(6,20)
    assert result == 120


def test_calculate_total_hours_for_20_weeks():
    result = calculate_total_hours(8,10)
    assert result == 80