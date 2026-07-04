def calculate_total_hours(weekly_hours, total_weeks):
    # TODO: 返回总学习小时数
    total_hours = weekly_hours * total_weeks
    return total_hours


def build_summary(name, weekly_hours, total_weeks):
    # TODO: 生成一段总结文字
    # 例如：陈晨计划每周学习 6 小时，持续 20 周，总计 120 小时。
    summary = (name,"计划每周学习",weekly_hours,"小时，持续",total_weeks,"周，总计",int(weekly_hours) * int(total_weeks),"小时。")
    return summary


def main():
    name = input("请输入你的名字：")
    weekly_hours = input("你每周计划学习多少小时？")
    total_weeks = input("你计划学习多少周？")

    try:
        # TODO: 转成数字
        total_hours = int(weekly_hours) * int(total_weeks)
        # TODO: 调用 build_summary()
        result = build_summary(name, weekly_hours, total_weeks)
        # TODO: print() 输出结果
        print("你好",name,"你的总学习时间为：",total_hours,"小时")
    except ValueError:
        print("学习小时数和学习周数都必须输入数字。")


if __name__ == "__main__":
    main()