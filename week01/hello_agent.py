"""第一个 Python 程序：让未来的 Agent 认识它的开发者。"""


def build_greeting(name: str, goal: str) -> str:
    """根据学习者的名字和目标生成欢迎语。"""
    clean_name = name.strip() or "同学"
    clean_goal = goal.strip() or "学习 Agent 开发"

    return (
        f"\n你好，{clean_name}！\n"
        f"你的目标是：{clean_goal}\n"
        "今天，我们先让第一段 Python 代码成功运行。\n"
        "不着急理解所有代码——能运行、敢修改，就是很好的开始。"
    )


def main() -> None:
    """接收用户输入，并显示欢迎语。"""
    print("=== 企业知识库 Agent 学习项目 ===")
    name = input("请输入你的名字：")
    goal = input("你为什么想学习 Agent 开发？：")
    print(build_greeting(name, goal))


if __name__ == "__main__":
    main()
