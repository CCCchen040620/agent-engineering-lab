name = input("请输入你的名字：")
weekly_hours = input("你每周计划学习多少个小时？")

try:
    total_hours = int(weekly_hours) * 20
    print("你好，",name)
    print("按照你的计划，20周一共学习",total_hours,"小时")
except ValueError:
    print("学习时间请输入数字，比如6或8。")


