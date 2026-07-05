# 错误档案

开发者不是不报错的人，而是越来越会读报错的人。

## 错误记录模板

日期：

我执行的操作：

```text
把命令或操作写在这里
```

完整报错：

```text
把报错写在这里
```

原因：

解决办法：

下次如何更快定位：

## 阶段错误复盘

### 1. ModuleNotFoundError: No module named 'week02'

原因：直接运行带包导入的文件时，Python 没有按项目模块方式查找。

解决：使用 `python -m week02.local_document_search` 运行模块。

学到：带 `from week02.xxx import xxx` 的代码，更适合用 `python -m` 运行。

### 2. pytest 读取 input() 报错

原因：测试导入文件时，文件最外层的 `input()` 被执行。

解决：把交互逻辑放进 `main()`，并使用 `if __name__ == "__main__": main()`。

学到：可测试代码应该避免导入时自动执行交互逻辑。

### 3. ResponseValidationError

原因：接口声明返回 `Document` 模型，但实际返回的是字符串列表或缺少字段的字典。

解决：让返回数据符合 Pydantic 模型结构，例如补充 `id` 字段。

学到：`response_model` 会校验接口返回值。

### 4. 测试因为真实 JSON 数据变化而失败

原因：手动新增/删除文档后，测试还假设真实文件里固定有 4 条数据。

解决：使用 `tmp_path` 和 `dependency_overrides` 隔离测试数据。

学到：测试应该尽量避免依赖会变化的真实数据。

### 5. FastAPI dependency_overrides 不生效

原因：代码里直接调用 `get_documents_file_path()`，没有使用 `Depends()`。

解决：改成 `file_path: str = Depends(get_documents_file_path)`。

学到：FastAPI 的依赖替换必须配合 `Depends()` 使用。