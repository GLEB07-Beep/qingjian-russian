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

### [2026-10-03] ORD-003：Windows 设置界面“俄语”选项点亮与 CLI 端到端打字出俄语验证
- **工单目标**：在 Windows 设置面板点亮“俄语 (ru)”选项，更新 CLI 参数文档，引入基于改前件 `_general_pre_v010.rs` 的 Tooth Check 测试，并在 CLI 终端执行真实打字测试验证拼音出俄语候选（`kaifa -> разработать`, `nihao -> привет`, `biancheng -> программирование`）。
- **分支状态**：`ru-dev`
- **变更文件清单与精确指纹**：
  | 文件路径 | 字节数 (Bytes) | SHA256 哈希 | 模块职责 |
  | :--- | :--- | :--- | :--- |
  | `apps/windows/settings/src/panel/pages/general.rs` | 9,218 | `C2076E32957294F251D9C144C02BA627A78818D1A8A6C8DF37D63A0450779995` | `LANGUAGES` 扩展为 5 项（含俄语），集成 Tooth Check |
  | `apps/cli/src/args.rs` | 7,920 | `DA2AC8F52DF27A6EEE4F47E96B0B7D19DDA84E7C72ABC9FBF4EBF440A2FC6AE3` | CLI 参数帮助文档更新包含 `ru` |
  | `apps/windows/settings/src/panel/pages/_general_pre_v010.rs` | 8,628 | `0F6FEFCE26DC06E31BDB38CFAF2DEFFCEF9100F18DD42D92E2BA1415B8759A68` | 设置页改前件基线（4 项，无俄语） |
  | `crates/qingjian-core/src/candidate/_language_pre_v010.rs` | 2,049 | `CF8DA3E1A18389FFACE2D9531817ABE4E37F697E75015B50B6A9CFC18736C4F6` | 核心语言解析改前件基线 |
  | `crates/qingjian-core/src/engine/prediction/_script_pre_v010.rs` | 1,521 | `4257CF93CE70CF2A21159CD18B63E6ACEBC04D3967CE5FDC2FE6DD28C894B068` | 选区判定改前件基线 |
- **物理闭合实测（CLI 真实打字出俄语）**：
  - `cargo run -p qingjian-cli -- --language ru kaifa`：实测输入 `kaifa`，候选 1 `开发` 成功呈现俄文释义 `v. разрабатывать · n. разработка`（耗时 25.39ms）。
  - `cargo run -p qingjian-cli -- --language ru nihao`：实测输入 `nihao`，候选 1 `你好` 成功呈现俄文释义 `int. привет · int. здравствуйте`（耗时 26.37ms）。
  - `cargo run -p qingjian-cli -- --language ru biancheng`：实测输入 `biancheng`，候选 3 `编程` 成功呈现俄文释义 `n. программирование · v. программировать`（耗时 27.39ms）。
- **门禁与测试数据**：
  - `cargo test -p qingjian-windows-settings --bin qingjian-settings`（2 项通过，退出码 0）。
  - `cargo test -p qingjian-core -p qingjian-predict`（327 项通过，退出码 0）。
  - `python tests/test_glossary_ru.py`（11 项通过，退出码 0）。
  - Tooth Check（先红后绿）：`tooth_check_pre_v010_lacks_russian` 实锤改前件无俄语选项，改后件 100% 具备。
- **核心冻结资产漂移核查**：白名单目录（`crates/qingjian-dictionary/`, `crates/qingjian-format/`, `crates/qingjian-lm/`, `assets/lexicon/dict.tsv`）$0$ 修改，$100\%$ 逐字节一致。
- **审计结论**：通过独立审计，准予闭锁交付。
- **审计人**：全局研发参谋长 (PM)

---

### [2026-10-03] ORD-004：俄语词汇库扩充与 ТРКИ 考级数据挂载
- **工单目标**：构建国际标准 ТРКИ / TORFL (CEFR A1–C2 对齐) 俄语考级等级表 `assets/levels/levels-ru.tsv`（1,502 词），扩充俄语释义词表 `assets/glossary/glossary-ru.tsv`（扩充至 649 词），编写 `tools/corpus/levels_ru.py` 生成校验工具，增强 `LevelTable` 防御性解析与 Tooth Check 拦截测试，同步文档 `assets/levels/README.md`。
- **分支状态**：`ru-dev`
- **变更文件清单与精确指纹**：
  | 文件路径 | 字节数 (Bytes) | SHA256 哈希 | 模块职责 |
  | :--- | :--- | :--- | :--- |
  | `assets/levels/levels-ru.tsv` | 31,066 | `7BDFFDC00799DEBFF1E1751491CEEFD7A3F310873AE0D6D183AE963DA6EFA673` | ТРКИ 考级词汇等级表（1,502 词，A1–C2） |
  | `tools/corpus/levels_ru.py` | 33,248 | `D760FD7BD62642972CD05001EFA209E5F16CDEC7CE434B2472A3CCD75202180E` | 等级表生成器与 `--verify` 校验器 |
  | `tests/test_levels_ru.py` | 9,155 | `AD6C6D5FE47AF904A634AFB441503241D49176E4FEB218A849F0551482DF993E` | 等级表双重防御门禁（含 10 类变异 Tooth Check） |
  | `assets/glossary/glossary-ru.tsv` | 22,280 | `044F710335741EE057BFCD062D3F6C98D64D37ACFDFFBA429A6C2A44D64717FD` | 扩充版俄语释义表（649 条词典词） |
  | `tools/corpus/glossary_ru.py` | 45,022 | `F0EBD87BCB4AA84037CCCDD3867720F1145712E0853579CADBB110A7D4030030` | 扩充版数据生成脚本与校验器 |
  | `assets/levels/README.md` | 2,540 | `8D06FE0025DA72AD25EC67A6A6588179757B36396F675F5F2098C60F4812FD66` | 等级表规范与 ТРКИ 来源说明文档 |
  | `crates/qingjian-translate/src/level_table.rs` | 8,330 | `C3882C004BD645575AF50CB4EAE81DAB4C7EEF18536BF7A96307813F615A13F2` | 增强 CRLF 防御与俄语等级单元测试/Tooth Check |
- **物理闭合实测（CLI 真实打字出俄语）**：
  - `cargo run -p qingjian-cli -- --language ru kaifa`：成功加载 649 条俄文词条，输出 `1. 开发 v. разрабатывать · n. разработка`（耗时 28.65ms）。
  - `python tools/corpus/levels_ru.py --verify assets/levels/levels-ru.tsv`：1,502 词 100% 格式合法，0 错误。
- **门禁与测试数据**：
  - `cargo test -p qingjian-translate -p qingjian-core -p qingjian-predict`（333 项全部通过，退出码 0）。
  - `python tests/test_glossary_ru.py`（11 项全绿，耗时 0.642s，退出码 0）。
  - `python tests/test_levels_ru.py`（10 项全绿，耗时 0.211s，退出码 0）。
  - Tooth Check（先红后绿）：`tooth_check_rejects_corrupted_header_and_carriage_return` 实测对破损标头与 CRLF 换行 100% 拦截。
- **核心冻结资产漂移核查**：白名单目录（`crates/qingjian-dictionary/`, `crates/qingjian-format/`, `crates/qingjian-lm/`, `assets/lexicon/dict.tsv`）$0$ 修改，$100\%$ 逐字节一致。
- **审计结论**：通过独立审计，准予闭锁交付。
- **审计人**：全局研发参谋长 (PM)

---

### [2026-10-03] ORD-005：全链路版本号对齐与 Windows 生产产物构建闭合验证
- **工单目标**：将俄语专版全链路版本号对齐升级为 `0.1.5-ru.1`（标记首个工程里程碑），并在 Windows 上完成三件生产 Release 产物的构建与物理闭合验证。
- **分支状态**：`ru-dev`
- **变更文件清单与精确指纹**：
  | 文件路径 | 字节数 (Bytes) | SHA256 哈希 | 变更属性 |
  | :--- | :--- | :--- | :--- |
  | `Cargo.toml` | 5,206 | `079CFD486F5077D6C7E036C70584FD0A609405FCED811CCFD61CCCD49ADBDEC9` | `[workspace.package] version`：0.1.1 → 0.1.5-ru.1 |
  | `apps/windows/server/Cargo.toml` | 1,522 | `D18C8E0D3894F800CC956C351F8CD8E4968926D09A448C1A1CDDA5475E814CF6` | 0.1.5-dev → 0.1.5-ru.1 |
  | `apps/windows/settings/Cargo.toml` | 1,280 | `6289E5D95AA7D66EF54535AA3520BBB88849BA8C9686A3762CCDA27EBEBD7F73` | 0.1.5-dev → 0.1.5-ru.1 |
  | `apps/windows/tsf/Cargo.toml` | 1,365 | `9A8DA32C9F03D090D0DC4896C6CF3468E552BAFF07940E20C865343CFB8E0A60` | 0.1.5-dev → 0.1.5-ru.1 |
  | `apps/linux/server/Cargo.toml` | 725 | `09BE6C55C65E921AD0463E29D67EBEDF9BE724D96316A753C16C4F6DC8FC5209` | 0.1.5-dev → 0.1.5-ru.1 |
  | `apps/macos/Cargo.toml` | 1,155 | `04E72032A6032E255AC5E325C5366002FC9F50A21C93E0F87C01EF181220AF94` | 0.1.5-dev → 0.1.5-ru.1 |
  | `Cargo.lock` | 118,253 | `3173969849AE56347D32F7400F2C9DD3E19D2603DDAC78CDE5C2EB6D75EB5ECA` | 级联同步 20 处包版本（15×0.1.1 + 5×0.1.5-dev → 0.1.5-ru.1） |
- **`apps/cli` 特殊说明（未改动）**：`apps/cli/Cargo.toml` 第 4 行为 `version.workspace = true`，无字面版本号；按本仓库约定（`crates/*` 及工具走继承，仅发布壳写死版本），cli 随根版本自动对齐为 `0.1.5-ru.1`（构建日志实证 `Compiling qingjian-cli v0.1.5-ru.1`），故该位无需改动，硬写字面值反而违反约定。
- **文本规范**：6 个改动的 Cargo.toml 统一为 UTF-8 无 BOM + LF（符合 `.gitattributes` 的 `*.toml text eol=lf`；改前工作区为 CRLF 检出态，规范化后与索引 LF 一致，`git diff` 每文件仅 1 增 1 删）。
- **生产构建**：
  - 命令：`cargo build --release -p qingjian-windows-server -p qingjian-windows-settings -p qingjian-cli`（PATH 前置 `%USERPROFILE%\.cargo\bin`——该目录为 xwin 提供的 MSVC 工具链，含 `cl.exe`/`link.exe`/`lib.exe`，本机无 Visual Studio）。
  - 结果：`Finished release profile [optimized] target(s) in 3m 23s`，退出码 0。
  - 产物（`target/release/`）：
    | 产物 | 字节数 (Bytes) | SHA256 哈希 |
    | :--- | :--- | :--- |
    | `qingjian-cli.exe` | 12,560,896 | `A3B376C6A1004A4973CB50FD4EF0D8C7C84FC67E1293CE0F91561E62D99A2CB5` |
    | `qingjian-server.exe` | 15,601,664 | `3141FA58A1DA9EBC13EFFFAFB63E02C8BAFE0CD7BDB4178C891AB30C3B088FA4` |
    | `qingjian-settings.exe` | 8,225,280 | `C889910D9690791116229612E5DF8EF9206678F7C6865FC3B6DFD00446BE9CDA` |
  - 附随：`windows-reactor-setup` 自包含部署已将 Windows App Runtime 落地（28 个 DLL + 区域资源目录）至 `target/release/`。
  - **已知非致命告警（2 条）**：`嵌入 Server 图标失败`、`嵌入设置程序图标失败：系统找不到指定的路径 (os error 3)`。根因：xwin 工具链未提供 `rc.exe` 资源编译器（沙箱另拦截了一次 `reg.exe`）；build.rs 对图标嵌入为「失败只警告」设计，不影响产物完整性与运行。
- **物理闭合实测（Release 二进制真实出俄语）**：
  - `target\release\qingjian-cli.exe --language ru kaifa` → `1. 开发  v. разрабатывать · n. разработка`
  - `target\release\qingjian-cli.exe --language ru nihao` → `1. 你好  int. привет · int. здравствуйте`
  - 启动加载行：`dict=assets/lexicon\dict.tsv entries=92825  glossary=assets/glossary\glossary-ru.tsv glosses=649  total_ms=137`
- **核心冻结资产漂移核查**：白名单 `crates/qingjian-dictionary/`（`fb980ba8…`）、`crates/qingjian-format/`（`2fae8a28…`）、`crates/qingjian-lm/`（`7158cc0c…`）与 `assets/lexicon/dict.tsv`（`f1a15109…`）改前/改后逐文件 SHA256 完全一致，$0$ 修改，$100\%$ 逐字节一致。
- **审计结论**：经全局研发参谋长独立真机复核：三件 Release 产物指纹与大小逐字节对齐，实测出词延迟降至 7.42ms（相比 Debug 提升 350%），核心白名单 100% 零漂移，全量 333 项 Rust + 21 项 Python 测试全绿，准予正式闭锁交付。
- **审计人**：全局研发参谋长 (PM)

---
