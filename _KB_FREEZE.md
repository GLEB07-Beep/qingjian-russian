# 青简·俄语专版 (Qingjian-RU) 封版账本 (Freeze Ledger)

本文档为工程质量与交付审计的唯一权威不可逆记账载体。
每次工单交付，必须如实记录工单编号、变更文件、精确字节数、SHA256 哈希、测试结论与产物摘要，形成永久可追溯的工程审计铁证。

---

## 核心冻结资产白名单 (Frozen Assets Whitelist)
以下核心算法与资产属于白名单保护对象，在未下发专项重构工单前，改前件、收工件必须保持 100% 逐字节 SAME：
- `crates/qingjian-dictionary/`：底层词库加载与查询逻辑
- `crates/qingjian-format/`：`.qj` 二进制容器布局与哈希索引算法
- `crates/qingjian-lm/`：Bigram 语言模型 Viterbi 核心求解
- `assets/lexicon/dict.tsv`：基础中文词典底座（只读）

---

## 历史工单流水账本 (Ledger Entries)

### [2026-10-03] ORD-000：项目立项与工程基线初始化
- **工单目标**：从上游 `qingjian-team/qingjian` 独立 Fork，建立 `Qingjian-RU`（青简·俄语专版）工程基线，配置 `upstream` 远程追踪，切换 `ru-dev` 开发分支。
- **分支状态**：`ru-dev`
- **上游基线 Commit**：`origin/main` (`HEAD`)
- **审计结论**：基线平铺完成，工作区状态 $100\%$ Clean，前序准备完毕。
- **审计人**：全局研发参谋长 (PM)

---

### [2026-10-03] ORD-001：俄语数据生成管线与种子释义表产出
- **工单目标**：完成俄语数据管线脚本开发、首版俄语种子释义表构建以及双重防御性门禁（含 Tooth Check 先红后绿拦截测试）。
- **分支状态**：`ru-dev`
- **变更文件清单与精确指纹**：
  | 文件路径 | 字节数 (Bytes) | SHA256 哈希 | 校验属性 |
  | :--- | :--- | :--- | :--- |
  | `tools/corpus/glossary_ru.py` | 25,200 | `cd414d0843cc992661cd5c7229c9bd77e30c8138134ed1c63b4b0e54559002f1` | UTF-8 / LF / 零三方依赖 |
  | `assets/glossary/glossary-ru.tsv` | 7,885 | `2fcceaacbaeee6f3f8b784b6721f44c9ef78f0db2d5657771386badc5d7f28d8` | 234 词 / 无 BOM / 码点升序 |
  | `tests/test_glossary_ru.py` | 9,820 | `024ef197a59c0b0cab9a6f8c73c9cf7e4d241ea50b9aa4be23880f8834ef15a5` | 双重门禁套件 |
- **门禁与测试数据**：
  - 快档回归门：`python tests/test_glossary_ru.py`（11 用例全绿，耗时 0.642s，退出码 0）。
  - 先红后绿验证（Tooth Check）：实测注入 10 种变异（BOM、CRLF、非法词性、英语混入、未译汉字、乱序、超长、动词变格等），拦截率 100%。
- **核心冻结资产漂移核查**：白名单目录（`crates/qingjian-dictionary/`, `crates/qingjian-format/`, `crates/qingjian-lm/`, `assets/lexicon/dict.tsv`）$0$ 修改，$100\%$ 逐字节一致。
- **审计结论**：通过独立审计，准予闭锁交付。
- **审计人**：全局研发参谋长 (PM)

---
