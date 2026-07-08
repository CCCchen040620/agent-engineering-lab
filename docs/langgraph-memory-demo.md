# LangGraph Memory Demo 学习笔记

这份文档记录 LangGraph memory/checkpoint 的最小练习。

当前练习文件：

```text
week09/langgraph_memory_demo.py
```

对应测试文件：

```text
tests/test_langgraph_memory_demo.py
```

## 1. 本节目标

这一节的目标是理解：

```text
同一个 thread_id 下，Graph 可以接上之前的状态。
不同 thread_id 之间，状态互相隔离。
```

也就是说，Agent 不再只是单轮请求，而是开始具备“会话状态”的雏形。

## 2. `thread_id` 是什么

`thread_id` 可以理解成：

```text
conversation_id
```

它用来区分不同对话。

例如：

```text
thread-1
thread-2
```

就是两段不同的对话。

同一个 `thread_id` 会读取之前保存的 State。

不同 `thread_id` 会互相隔离，不会共享记忆。

## 3. `InMemorySaver` 是什么

代码中使用：

```python
from langgraph.checkpoint.memory import InMemorySaver
```

然后：

```python
checkpointer = InMemorySaver()
graph_builder.compile(checkpointer=checkpointer)
```

`InMemorySaver` 的作用是：

```text
把 Graph 的状态临时保存在内存中。
```

当再次用同一个 `thread_id` 调用 Graph 时，LangGraph 可以从 checkpointer 中恢复之前的 State。

## 4. 为什么同一个 thread 能记住名字

第一次调用：

```text
message = "我叫陈晨"
thread_id = "thread-1"
```

Graph 保存：

```python
{
    "messages": ["我叫陈晨"],
    "remembered_name": "陈晨"
}
```

第二次调用：

```text
message = "我叫什么？"
thread_id = "thread-1"
```

因为 `thread_id` 仍然是 `thread-1`，所以 Graph 能拿到之前保存的：

```python
remembered_name = "陈晨"
```

因此回答：

```text
你叫陈晨。
```

## 5. 为什么不同 thread 不会共享记忆

如果第一次调用：

```text
message = "我叫陈晨"
thread_id = "thread-1"
```

第二次调用：

```text
message = "我叫什么？"
thread_id = "thread-2"
```

因为 `thread-2` 是另一段对话，所以它不会读取 `thread-1` 的状态。

因此回答：

```text
我还不知道你的名字。
```

这说明 memory 是按照 `thread_id` 隔离的。

## 6. `Annotated[list[str], add]` 的作用

代码中有：

```python
from operator import add
from typing import Annotated

messages: Annotated[list[str], add]
steps: Annotated[list[str], add]
```

这里的重点是：

```text
列表字段更新时，使用追加合并，而不是直接覆盖。
```

例如第一轮：

```python
messages = ["我叫陈晨"]
```

第二轮同一个 thread 新增：

```python
messages = ["我叫什么？"]
```

因为使用了：

```python
Annotated[list[str], add]
```

最终结果会变成：

```python
["我叫陈晨", "我叫什么？"]
```

而不是只剩：

```python
["我叫什么？"]
```

所以它的作用是告诉 LangGraph：

```text
这个字段不要覆盖，要累加。
```

## 7. 这次练习踩到的小坑

一开始判断逻辑是：

```python
if "我叫" in latest_message:
```

但问题：

```text
我叫什么？
```

里面也包含：

```text
我叫
```

所以程序错误地把“什么？”当成了名字。

修复方式是：

```text
更具体的规则放前面，更宽泛的规则放后面。
```

也就是先判断：

```python
if "我叫什么" in latest_message:
```

再判断：

```python
elif "我叫" in latest_message:
```

这个经验和之前关键词提取中的“具体词优先”是一样的。

## 8. `InMemorySaver` 的局限

`InMemorySaver` 只是内存记忆。

它的局限是：

- 程序重启后记忆会消失。
- 不适合生产环境长期保存。
- 不能跨机器共享。
- 不能作为正式数据库使用。

它适合：

- 本地学习
- 快速 demo
- 理解 checkpointer 工作方式

如果要做正式企业级 Agent，后续应该考虑：

- SQLite checkpointer
- PostgreSQL checkpointer
- 和项目现有 conversation/message 表结合

## 9. 和当前企业知识库 Agent 的关系

当前正式 LangGraph Agent 还是单轮请求为主。

也就是说：

```text
用户每问一次，Agent 执行一次完整流程。
```

这次 memory demo 说明未来可以让 Agent 支持：

- 多轮对话
- 同一个会话中记住上下文
- 根据历史问题继续回答
- 保存 conversation_id / thread_id
- 读取之前的 messages

未来可以把：

```text
thread_id
```

和项目中的：

```text
Conversation
Message
```

结合起来。

## 10. 当前阶段理解

我现在理解：

- `thread_id` 用来区分会话。
- checkpointer 根据 `thread_id` 保存和恢复 State。
- `InMemorySaver` 是最简单的内存版 checkpointer。
- `Annotated[list[str], add]` 可以让列表字段追加，而不是覆盖。
- memory 让 Agent 从单轮请求走向多轮会话。

但这个 demo 还不是正式长期记忆。

它只是帮助我理解 LangGraph memory 的最小机制。

## 11. 下一步方向

下一步可以继续学习：

1. 把 `thread_id` 加入正式 LangGraph Agent API。
2. 让前端传入 conversation_id。
3. 把历史消息保存到 SQLite。
4. 研究 LangGraph 持久化 checkpointer。
5. 决定哪些信息应该进入短期记忆，哪些信息应该进入数据库长期存储。
