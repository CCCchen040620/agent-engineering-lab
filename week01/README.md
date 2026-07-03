# 第 1 周：第一次和 Python 对话

开始前先完成 [环境检查单](environment-checklist.md)。

## 第 1 课目标

今天结束时，你只需要做到：

- 知道 Python 文件以 `.py` 结尾。
- 知道终端可以运行 Python 文件。
- 能修改变量并观察输出变化。
- 遇到报错时，愿意把完整信息保存下来。

`hello_agent.py` 里已经出现了函数和类型标注。今天把它们当作一个“输入信息、产生欢迎语的盒子”即可，后面会逐项拆开。

## 任务一：运行程序

在项目根目录运行：

```powershell
python week01/hello_agent.py
```

观察顺序：

1. 终端先显示标题。
2. 程序等待你输入名字。
3. 程序等待你输入学习目标。
4. 程序把信息组合成欢迎语。

## 任务二：完成独立练习

打开 `week01/exercise_01.py`：

1. 修改 `learner_name`。
2. 修改 `weekly_hours`。
3. 运行：

   ```powershell
   python week01/exercise_01.py
   ```

4. 完成文件底部的挑战题。

## 任务三：建立第一个 Git 存档

确认前两个任务完成后，在项目根目录依次输入：

```powershell
git init
git add .
git commit -m "chore: start agent learning journey"
```

如果 Git 提示没有配置姓名或邮箱，先把完整提示保存到错误档案并发给导师，我们会在下一步理解后再配置。

## 今天需要理解的三个词

### 变量

变量像贴了标签的盒子：

```python
learner_name = "小明"
```

`learner_name` 是标签，`"小明"` 是盒子里的数据。

### 字符串

用引号包围的文字叫字符串：

```python
"企业知识库 Agent"
```

### 输出

`print()` 会把信息显示到终端：

```python
print("你好")
```

## 如果报错

先不要反复乱改：

1. 找到报错最后几行。
2. 看其中是否出现文件名和行号。
3. 把完整报错复制到 `docs/error-log.md`。
4. 连同你的代码和猜测一起发给导师。

## 完成标准

- 欢迎程序成功运行。
- 独立练习显示你的真实信息。
- 挑战题能显示第一个项目名称。
- [第 1 课小测](quiz.md)至少答对 4 题。
- 完成一次学习日志。
