# 检索模式耗时观察记录

评测日期：2026-07-07

## 评测问题

```text
员工可以远程办公吗？
```

## 参数

```text
min_score = 0.8
top_k = 3
```

## 检索模式耗时

| 检索模式 | 耗时 |
|---|---:|
| `keyword` | 0.000s |
| `vector` | 0.307s |
| `embedding` | 40.259s |
| `precomputed_embedding` | 2.191s |

## 观察结果

`keyword` 模式最快，因为它只使用 SQLite `LIKE` 查询，不调用模型。

`vector` 模式也较快，因为它使用本地 jieba 分词、词频向量和余弦相似度，不调用 embedding 模型。

`embedding` 模式耗时最高，因为它会在每次查询时为用户问题和所有 chunks 实时调用 Ollama `bge-m3` 生成 embeddings。

`precomputed_embedding` 模式明显快于实时 `embedding`，因为它只需要为用户问题生成 embedding，chunks 的 embeddings 已经在入库或 backfill 阶段提前保存到 SQLite。

## 工程结论

实时 embedding 检索适合作为学习和验证原型，但不适合作为知识库规模增长后的默认在线检索方式。

更合理的方式是：

```text
文档入库阶段：为 chunks 生成 embeddings 并保存
用户查询阶段：只为 query 生成 embedding
检索阶段：对 query embedding 和已保存的 chunk embeddings 计算相似度
```

这也是后续升级到 PostgreSQL + pgvector 或其他向量数据库的基础思路。
