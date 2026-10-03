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

### [2026-10-03] ORD-002：Rust Core 语言枚举扩展与俄语预测清洗
- **工单目标**：在 Rust 核心引擎接入 `Language::Russian`（代码 `"ru"` 与别名解析），选区翻译判定扩展西里尔文支持，云端释义增加俄语系统 Prompt 与西里尔字符合法性过滤器，对齐全工程多语言 exhaustiveness 匹配，建立双重防御门禁。
- **分支状态**：`ru-dev`
- **变更文件清单与精确指纹**：
  | 文件路径 | 字节数 (Bytes) | SHA256 哈希 | 模块职责 |
  | :--- | :--- | :--- | :--- |
  | `crates/qingjian-core/src/candidate/language.rs` | 2,949 | `0F813C76F4F775830B1B03D845F1E9752BAF072AFC23FA4468514E7FC7D7CBA1` | Language 枚举与别名解析 |
  | `crates/qingjian-core/src/engine/prediction/script.rs` | 4,735 | `BCF19B2BA4193A7D9BD5AB9CFABA184297EEAFD0B860D0EBB6E0DEB1F48E8C12` | 西里尔字母范围侦测与目标语言判定 |
  | `crates/qingjian-predict/src/gloss/prompt.rs` | 14,740 | `861D62653F225F46CCACC9E8A6138CA2CE79315786B845262EF3B2A3414A375E` | 俄语 LLM 提示词与西里尔清洗过滤器 |
  | `apps/windows/settings/src/panel/pages/usage.rs` | 7,547 | `4FE475F8943EE783D46CD49A216C12D217BA333F4D17DB8C01BF27988B2EFEBF` | Windows 统计页俄语名称穷尽匹配 |
  | `apps/macos/src/preferences/controls.rs` | 7,756 | `AC1679F0B1F38E9E277A2A6ED80BFAEAD08C5CA6DE7C544FB7B2870F0AFC2FC0` | macOS 偏好设置俄语名称穷尽匹配 |
  | `apps/windows/server/src/assembly/mod.rs` | 7,664 | `9256519D0691AEBFAA1E8AE74DD137FEC1351DB97B85DC04FEBB74066EAC667B` | Windows 词汇装配语言数组对齐 |
  | `apps/linux/server/src/assembly/mod.rs` | 6,480 | `9535F924F1C6E5F77D2FA04D18B632955FF922D7B568D8B597FAE0CA8210DC56` | Linux 词汇装配语言数组对齐 |
  | `apps/macos/src/host/mod.rs` | 9,052 | `D4E833CC682FDC9F8F8865AF34CA92BEFFE901727CD68F65EA0C5B04C51EE78A` | macOS 释义语言数组扩展对齐 |
- **门禁与测试数据**：
  - 快档回归门：`cargo test -p qingjian-core -p qingjian-predict`（327 项测试全部通过：Core 310 项全绿，Predict 17 项全绿，耗时 0.41s，退出码 0）。
  - 先红后绿验证（Tooth Check）：
    1. 改前件 `_language_pre_v010.rs` 对 `"ru"`/`"русский"` 拦截报 `UnknownLanguage` 失败；改后件 100% 成功解析。
    2. 改前件 `_script_pre_v010.rs` 对中俄混合文本错误判定为英文；改后件依据 `cyrillic > 0` 精准回译中文。
    3. 改前件 `_prompt_pre_v010.rs` 触发编译器 `non-exhaustive patterns` 硬拦截；改后件模式匹配全闭环。
- **核心冻结资产漂移核查**：白名单目录（`crates/qingjian-dictionary/`, `crates/qingjian-format/`, `crates/qingjian-lm/`, `assets/lexicon/dict.tsv`）$0$ 修改，$100\%$ 逐字节一致。
- **审计结论**：通过独立审计，准予闭锁交付。
- **审计人**：全局研发参谋长 (PM)

---
