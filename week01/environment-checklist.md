# 第 1 周环境检查单

先完成检查，不要一次安装一大堆工具。

## 1. Python 3.13

在终端输入：

```powershell
python --version
```

目标输出类似 `Python 3.13.x`。如果命令不存在，安装 Python 3.13 的 64 位版本，并在安装界面勾选“Add python.exe to PATH”。

## 2. 代码编辑器

建议使用 Visual Studio Code。打开当前文件夹后，应能在左侧看到 `README.md`、`week01` 和 `docs`。

暂时只安装官方 Python 扩展，不需要挑选主题或安装大量插件。

## 3. Git

在终端输入：

```powershell
git --version
```

目标输出类似 `git version 2.x.x`。Git 用来记录代码每次变化，像游戏存档一样。

## 4. 第一次运行

确保终端当前路径是本项目，然后输入：

```powershell
python week01/hello_agent.py
```

如果任何一步报错，把完整报错记录到 `docs/error-log.md`，再发给导师。

## 环境验收

- [ ] `python --version` 有正确输出
- [ ] 能在编辑器中看到项目文件
- [ ] `git --version` 有正确输出
- [ ] `hello_agent.py` 成功运行
