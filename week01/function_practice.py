def calculate_total_hours(weekly_hours, total_weeks):
    total_hours = weekly_hours * total_weeks
    return total_hours


def main():
    hours = int(input("你每周计划学习多少小时？"))
    weeks = int(input("你计划学习多少周？"))

    result = calculate_total_hours(hours, weeks)

    print(weeks, "周一共学习", result, "小时")


if __name__ == "__main__":
    main()