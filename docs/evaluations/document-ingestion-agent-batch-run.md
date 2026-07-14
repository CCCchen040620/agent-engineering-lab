# PostgreSQL 批量文档入库 Agent 验收报告

## 汇总

- 总用例数：8
- 通过数：8
- 失败数：0
- 通过率：1.0
- 检索层通过数：8
- 生成层通过数：7
- source 匹配数：8
- 检索后端：postgresql

## 明细

### migration_employee_handbook_safety_training

- 是否通过：是
- 失败原因：
- 文档标题：员工手册
- 问题：新员工什么时候完成安全培训？
- 期望 source：migration
- 实际 source：migration
- source 是否匹配：是
- 检索层是否通过：是
- 生成层是否通过：是
- 引用数量：3

# PostgreSQL 文档入库 Agent 验收报告

## 验收结论

- 是否通过：是
- 失败原因：
- 检索层是否通过：是
- 检索层失败原因：
- 生成层是否通过：是
- 生成层失败原因：

## 验收对象

- 文档标题：员工手册
- 问题：新员工什么时候完成安全培训？
- 检索后端：postgresql
- 检索模式：precomputed_embedding
- top_k：3
- min_score：0.6

## Agent 状态

- has_valid_context：是
- 是否兜底回答：否
- 是否引用目标文档：是
- Top1 是否引用目标文档：是
- 引用数量：3

## 回答

根据知识库资料，新员工入职后需要在 30 天内完成安全培训。

## 引用来源

- [1] 员工手册 - postgresql://chunk/13
  - 片段：新员工入职后需要在 30 天内完成安全培训。
- [2] PostgreSQL API 入库验收文档 - postgresql://chunk/4
  - 片段：员工参加外部培训需要提前提交申请。
- [3] PostgreSQL Agent 端到端验收文档 - postgresql://chunk/32
  - 片段：员工参加外部培训需要提前提交申请。

## 检索片段

- [1] 员工手册 - postgresql://chunk/13
  - 分数：0.8443818807770581
  - 片段：新员工入职后需要在 30 天内完成安全培训。
- [2] PostgreSQL API 入库验收文档 - postgresql://chunk/4
  - 分数：0.6841153549265351
  - 片段：员工参加外部培训需要提前提交申请。
- [3] PostgreSQL Agent 端到端验收文档 - postgresql://chunk/32
  - 分数：0.6841153549265351
  - 片段：员工参加外部培训需要提前提交申请。


### migration_leave_policy_annual_leave

- 是否通过：是
- 失败原因：
- 文档标题：请假制度
- 问题：年假需要提前几个工作日申请？
- 期望 source：migration
- 实际 source：migration
- source 是否匹配：是
- 检索层是否通过：是
- 生成层是否通过：是
- 引用数量：3

# PostgreSQL 文档入库 Agent 验收报告

## 验收结论

- 是否通过：是
- 失败原因：
- 检索层是否通过：是
- 检索层失败原因：
- 生成层是否通过：是
- 生成层失败原因：

## 验收对象

- 文档标题：请假制度
- 问题：年假需要提前几个工作日申请？
- 检索后端：postgresql
- 检索模式：precomputed_embedding
- top_k：3
- min_score：0.6

## Agent 状态

- has_valid_context：是
- 是否兜底回答：否
- 是否引用目标文档：是
- Top1 是否引用目标文档：是
- 引用数量：3

## 回答

根据知识库资料，年假需要提前 3 个工作日申请。

## 引用来源

- [1] 请假制度 - postgresql://chunk/17
  - 片段：年假需要提前 3 个工作日申请。
- [2] 请假制度 - postgresql://chunk/15
  - 片段：员工请假需要提前在系统中提交申请。
- [3] 加班制度 - postgresql://chunk/20
  - 片段：员工加班需要提前提交申请。

## 检索片段

- [1] 请假制度 - postgresql://chunk/17
  - 分数：0.9466492470085328
  - 片段：年假需要提前 3 个工作日申请。
- [2] 请假制度 - postgresql://chunk/15
  - 分数：0.8162550488126626
  - 片段：员工请假需要提前在系统中提交申请。
- [3] 加班制度 - postgresql://chunk/20
  - 分数：0.7707648326790153
  - 片段：员工加班需要提前提交申请。


### migration_remote_work_policy

- 是否通过：是
- 失败原因：
- 文档标题：远程办公制度
- 问题：每周可以申请几天远程办公？
- 期望 source：migration
- 实际 source：migration
- source 是否匹配：是
- 检索层是否通过：是
- 生成层是否通过：是
- 引用数量：3

# PostgreSQL 文档入库 Agent 验收报告

## 验收结论

- 是否通过：是
- 失败原因：
- 检索层是否通过：是
- 检索层失败原因：
- 生成层是否通过：是
- 生成层失败原因：

## 验收对象

- 文档标题：远程办公制度
- 问题：每周可以申请几天远程办公？
- 检索后端：postgresql
- 检索模式：precomputed_embedding
- top_k：3
- min_score：0.6

## Agent 状态

- has_valid_context：是
- 是否兜底回答：否
- 是否引用目标文档：是
- Top1 是否引用目标文档：是
- 引用数量：3

## 回答

根据知识库资料，员工每周可以申请**一天**远程办公。

## 引用来源

- [1] 远程办公制度 - postgresql://chunk/18
  - 片段：员工每周可以申请一天远程办公。
- [2] 混合标点制度 - postgresql://chunk/22
  - 片段：员工可以远程办公吗。
- [3] 远程办公制度 - postgresql://chunk/19
  - 片段：远程办公需要提前提交申请。

## 检索片段

- [1] 远程办公制度 - postgresql://chunk/18
  - 分数：0.9110665499805469
  - 片段：员工每周可以申请一天远程办公。
- [2] 混合标点制度 - postgresql://chunk/22
  - 分数：0.8150323453681046
  - 片段：员工可以远程办公吗。
- [3] 远程办公制度 - postgresql://chunk/19
  - 分数：0.7860784809437904
  - 片段：远程办公需要提前提交申请。


### migration_overtime_policy

- 是否通过：是
- 失败原因：
- 文档标题：加班制度
- 问题：员工加班需要提前做什么？
- 期望 source：migration
- 实际 source：migration
- source 是否匹配：是
- 检索层是否通过：是
- 生成层是否通过：是
- 引用数量：3

# PostgreSQL 文档入库 Agent 验收报告

## 验收结论

- 是否通过：是
- 失败原因：
- 检索层是否通过：是
- 检索层失败原因：
- 生成层是否通过：是
- 生成层失败原因：

## 验收对象

- 文档标题：加班制度
- 问题：员工加班需要提前做什么？
- 检索后端：postgresql
- 检索模式：precomputed_embedding
- top_k：3
- min_score：0.6

## Agent 状态

- has_valid_context：是
- 是否兜底回答：否
- 是否引用目标文档：是
- Top1 是否引用目标文档：是
- 引用数量：3

## 回答

根据知识库资料，员工加班需要提前提交申请。

## 引用来源

- [1] 加班制度 - postgresql://chunk/20
  - 片段：员工加班需要提前提交申请。
- [2] 请假制度 - postgresql://chunk/15
  - 片段：员工请假需要提前在系统中提交申请。
- [3] 会议室预约制度 - postgresql://chunk/6
  - 片段：员工预约会议室需要提前提交申请。

## 检索片段

- [1] 加班制度 - postgresql://chunk/20
  - 分数：0.916845112975258
  - 片段：员工加班需要提前提交申请。
- [2] 请假制度 - postgresql://chunk/15
  - 分数：0.8078459592416949
  - 片段：员工请假需要提前在系统中提交申请。
- [3] 会议室预约制度 - postgresql://chunk/6
  - 分数：0.7732794133999467
  - 片段：员工预约会议室需要提前提交申请。


### migration_mixed_punctuation_policy

- 是否通过：是
- 失败原因：
- 文档标题：混合标点制度
- 问题：主管审批后什么时候生效？
- 期望 source：migration
- 实际 source：migration
- source 是否匹配：是
- 检索层是否通过：是
- 生成层是否通过：是
- 引用数量：3

# PostgreSQL 文档入库 Agent 验收报告

## 验收结论

- 是否通过：是
- 失败原因：
- 检索层是否通过：是
- 检索层失败原因：
- 生成层是否通过：是
- 生成层失败原因：

## 验收对象

- 文档标题：混合标点制度
- 问题：主管审批后什么时候生效？
- 检索后端：postgresql
- 检索模式：precomputed_embedding
- top_k：3
- min_score：0.6

## Agent 状态

- has_valid_context：是
- 是否兜底回答：否
- 是否引用目标文档：是
- Top1 是否引用目标文档：是
- 引用数量：3

## 回答

根据【知识库资料】，主管审批后即时生效。

## 引用来源

- [1] 混合标点制度 - postgresql://chunk/25
  - 片段：主管审批后生效。
- [2] 加班制度 - postgresql://chunk/21
  - 片段：加班需要直属主管审批。
- [3] 设备借用制度 - postgresql://chunk/27
  - 片段：设备归还时需要管理员确认。

## 检索片段

- [1] 混合标点制度 - postgresql://chunk/25
  - 分数：0.9254083481978939
  - 片段：主管审批后生效。
- [2] 加班制度 - postgresql://chunk/21
  - 分数：0.7648984806635398
  - 片段：加班需要直属主管审批。
- [3] 设备借用制度 - postgresql://chunk/27
  - 分数：0.6336741884146775
  - 片段：设备归还时需要管理员确认。


### migration_equipment_policy

- 是否通过：是
- 失败原因：
- 文档标题：设备借用制度
- 问题：员工借用公司设备需要做什么？
- 期望 source：migration
- 实际 source：migration
- source 是否匹配：是
- 检索层是否通过：是
- 生成层是否通过：是
- 引用数量：3

# PostgreSQL 文档入库 Agent 验收报告

## 验收结论

- 是否通过：是
- 失败原因：
- 检索层是否通过：是
- 检索层失败原因：
- 生成层是否通过：是
- 生成层失败原因：

## 验收对象

- 文档标题：设备借用制度
- 问题：员工借用公司设备需要做什么？
- 检索后端：postgresql
- 检索模式：precomputed_embedding
- top_k：3
- min_score：0.6

## Agent 状态

- has_valid_context：是
- 是否兜底回答：否
- 是否引用目标文档：是
- Top1 是否引用目标文档：是
- 引用数量：3

## 回答

根据知识库资料，员工借用公司设备需要提交申请。

## 引用来源

- [1] 设备借用制度 - postgresql://chunk/26
  - 片段：员工借用公司设备需要提交申请。
- [2] 设备借用制度 - postgresql://chunk/27
  - 片段：设备归还时需要管理员确认。
- [3] 混合标点制度 - postgresql://chunk/22
  - 片段：员工可以远程办公吗。

## 检索片段

- [1] 设备借用制度 - postgresql://chunk/26
  - 分数：0.9175304896448284
  - 片段：员工借用公司设备需要提交申请。
- [2] 设备借用制度 - postgresql://chunk/27
  - 分数：0.6797069797891783
  - 片段：设备归还时需要管理员确认。
- [3] 混合标点制度 - postgresql://chunk/22
  - 分数：0.6785750814855401
  - 片段：员工可以远程办公吗。


### migration_visitor_policy

- 是否通过：是
- 失败原因：
- 文档标题：visitor_policy.txt
- 问题：访客进入办公区需要做什么？
- 期望 source：migration
- 实际 source：migration
- source 是否匹配：是
- 检索层是否通过：是
- 生成层是否通过：是
- 引用数量：3

# PostgreSQL 文档入库 Agent 验收报告

## 验收结论

- 是否通过：是
- 失败原因：
- 检索层是否通过：是
- 检索层失败原因：
- 生成层是否通过：是
- 生成层失败原因：

## 验收对象

- 文档标题：visitor_policy.txt
- 问题：访客进入办公区需要做什么？
- 检索后端：postgresql
- 检索模式：precomputed_embedding
- top_k：3
- min_score：0.6

## Agent 状态

- has_valid_context：是
- 是否兜底回答：否
- 是否引用目标文档：是
- Top1 是否引用目标文档：是
- 引用数量：3

## 回答

根据知识库资料，访客进入办公区需要完成以下事项：
1. 提前进行登记；
2. 由员工陪同进入。

## 引用来源

- [1] visitor_policy.txt - postgresql://chunk/29
  - 片段：访客需要由员工陪同进入办公区。
- [2] visitor_policy.txt - postgresql://chunk/28
  - 片段：访客进入办公区需要提前登记。
- [3] 会议室预约制度 - postgresql://chunk/6
  - 片段：员工预约会议室需要提前提交申请。

## 检索片段

- [1] visitor_policy.txt - postgresql://chunk/29
  - 分数：0.8831522991152381
  - 片段：访客需要由员工陪同进入办公区。
- [2] visitor_policy.txt - postgresql://chunk/28
  - 分数：0.83675712224587
  - 片段：访客进入办公区需要提前登记。
- [3] 会议室预约制度 - postgresql://chunk/6
  - 分数：0.6987181873275548
  - 片段：员工预约会议室需要提前提交申请。


### migration_sqlite_sample_policy

- 是否通过：是
- 失败原因：fallback_answer
- 文档标题：SQLite 迁移验收文档
- 问题：SQLite 迁移测试片段一是什么？
- 期望 source：migration
- 实际 source：migration
- source 是否匹配：是
- 检索层是否通过：是
- 生成层是否通过：否
- 引用数量：3

# PostgreSQL 文档入库 Agent 验收报告

## 验收结论

- 是否通过：是
- 失败原因：fallback_answer
- 检索层是否通过：是
- 检索层失败原因：
- 生成层是否通过：否
- 生成层失败原因：fallback_answer

## 验收对象

- 文档标题：SQLite 迁移验收文档
- 问题：SQLite 迁移测试片段一是什么？
- 检索后端：postgresql
- 检索模式：precomputed_embedding
- top_k：3
- min_score：0.6

## Agent 状态

- has_valid_context：是
- 是否兜底回答：是
- 是否引用目标文档：是
- Top1 是否引用目标文档：是
- 引用数量：3

## 回答

已检索到相关资料，但模型生成回答失败。请查看引用内容：
[1] SQLite 迁移测试片段一。
来源：SQLite 迁移验收文档
[2] SQLite 迁移测试片段二。
来源：SQLite 迁移验收文档
[3] 这是一条写入 PostgreSQL pgvector 的测试片段。
来源：PostgreSQL RAG 存储测试文档

## 引用来源

- [1] SQLite 迁移验收文档 - postgresql://chunk/10
  - 片段：SQLite 迁移测试片段一。
- [2] SQLite 迁移验收文档 - postgresql://chunk/11
  - 片段：SQLite 迁移测试片段二。
- [3] PostgreSQL RAG 存储测试文档 - postgresql://chunk/1
  - 片段：这是一条写入 PostgreSQL pgvector 的测试片段。

## 检索片段

- [1] SQLite 迁移验收文档 - postgresql://chunk/10
  - 分数：0.9249277211532178
  - 片段：SQLite 迁移测试片段一。
- [2] SQLite 迁移验收文档 - postgresql://chunk/11
  - 分数：0.8538545697960176
  - 片段：SQLite 迁移测试片段二。
- [3] PostgreSQL RAG 存储测试文档 - postgresql://chunk/1
  - 分数：0.640667133510261
  - 片段：这是一条写入 PostgreSQL pgvector 的测试片段。

