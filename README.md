<p align="center">
  <img src="assets/icon/qingjian-mark.svg" alt="青简图标" height="108">
</p>

<h1 align="center">青简 · 俄语专版 (Qingjian-RU)</h1>

<p align="center"><strong>好好输入，顺便多学一个俄语词。</strong><br>
<em>Нативный ввод пиньинь для изучающих русский язык — перевод на кириллице, части речи и уровни ТРКИ.</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Russian%20%7C%20%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-red?style=flat" alt="Russian">
  <img src="https://img.shields.io/badge/%D0%A2%D0%A0%D0%9A%D0%98%20(TORFL)-A1%E2%80%93C2-blue?style=flat" alt="TORFL Levels">
  <img src="https://img.shields.io/badge/Glossary-54%2C918%20Words-success?style=flat" alt="54k Words">
  <img src="https://img.shields.io/badge/Windows-10%2F11%20x64-blue?style=flat" alt="Windows 10/11">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue" alt="License: GPL-3.0-or-later"></a>
</p>

---

## 🌟 项目简介

**青简·俄语专版（Qingjian-RU）** 是一款专为**俄语学习者、翻译人员及中俄双语工作者**打造的开源原生 Windows 输入法。

在日常打字输入拼音时，输入法候选词侧边**实时呈现西里尔字母俄语翻译、规范词性标注（动词不定式原形、名词单数第一格、阳性形容词等）以及 ТРКИ (TORFL) 俄语考级难度标签**。让背单词与语法巩固自然融入到微信聊天、写文档、写代码的每一次敲击中。

```text
> ni
 1. 你       pron. ты
 2. 尼       n. монахиня
 3. 妮       n. девочка

> kaifa
 1. 开发     v. разрабатывать · n. разработка

> nihao
 1. 你好     int. привет · int. здравствуйте
```

---

## ✨ 核心特性

- 📚 **54,918 条高质量西里尔俄语词库**：
  - 严谨覆盖 **1,000+ 高频基础汉字单字**（你我他她、是否在有、好大多少、听说读写等），彻底消灭常见字无标注盲区。
  - 收录日常交际、科技办公、工程算法等数万条生活与技术词汇。
- 🎓 **ТРКИ (TORFL / CEFR) 考级难度分级追踪**：
  - 挂载全套 ТРКИ 俄语词汇考级数据库（A1 初级到 C2 母语级）。打字时自动标记词汇等级，量化词汇量。
- ⚡ **9.2 万全量基础拼音词库 + 整句预测**：
  - 内置完整 9.2 万基础词库与 Viterbi 解码算法，全拼、简拼（如 `wjszd` -> 我就是知道）、长句连打行云流水。
- 🪟 **原生 Windows Text Services Framework (TSF) 架构**：
  - 基于微软官方 TSF 规范深度开发，UI 采用现代 WinUI 3 原生渲染，毫秒级响应，告别卡顿与选框漂移。
- 🛡️ **绝对离线与隐私安全**：
  - 拼音转换与词典检索 100% 在本机本地完成；零弹窗、零广告、无后台网络上传，纯粹干净。

---

## 🚀 极速下载与安装体验

### 方式一：下载开箱即用便携绿色包（推荐）

1. 从 [Releases 页面](../../releases) 下载最新版的 **`Qingjian-RU-v0.1.5-windows-x64.zip`**；
2. 解压压缩包到任意本地文件夹（例如 `D:\Software\Qingjian-RU`）；
3. 鼠标右键以**管理员身份运行**里面的 **`install.bat`**：
   - 脚本将自动完成 TSF 注册与服务启动；
4. 按键盘 **`Win + 空格`** 切换到 **“青简”** 输入法，即可开始沉浸式俄语打字体验！

*(如需卸载，右键管理员运行 `uninstall.bat` 即可一键干净清理输入法注册)*

---

### 方式二：从源码编译构建

本仓库采用 Rust 开发，构建系统使用 Cargo：

```powershell
# 1. 克隆代码仓库
git clone -b ru-dev https://github.com/GLEB07-Beep/qingjian-ru.git
cd qingjian-ru

# 2. 编译 Release 组件
$env:QINGJIAN_UIACCESS = "0"
cargo build --release -p qingjian-windows-server -p qingjian-windows-settings -p qingjian-cli -p qingjian-windows-tsf

# 3. 运行命令行端到端测试
target\release\qingjian-cli.exe --language ru ni
target\release\qingjian-cli.exe --language ru kaifa
```

---

## ⚙️ 设置与语言切换

运行 `qingjian-settings.exe`，可在可视化面板中进行如下个性化定制：

- **学习语言切换**：随时在 俄语 (ru) / 英语 (en) / 日语 (ja) / 西班牙语 (es) 或“不显示译文”间切换；
- **候选词数量**：支持每页 5 ~ 9 个候选词；
- **中英文一键切换**：打字过程中单击键盘 `Shift` 键即可一键切换中英文输入模式。

---

## 📖 架构与贡献

- `crates/qingjian-core`: 拼音切分、输入方案与多语言引擎核心
- `crates/qingjian-translate`: 释义表加载、ТРКИ 考级等级解析器与多层翻译器
- `apps/windows/`: Windows TSF 动态库、后台守护进程与 WinUI 设置面板
- `assets/glossary/glossary-ru.tsv`: 俄语西里尔释义数据库（严格 UTF-8 无 BOM、LF 换行、Unicode 升序排序）
- `assets/levels/levels-ru.tsv`: ТРКИ (TORFL A1–C2) 俄语考级等级表

欢迎提交 Issue 和 Pull Request 为俄语词库与输入体验添砖加瓦！

---

## 📄 许可证与致谢

- 本项目基于上游优秀开源项目 [qingjian-team/qingjian](https://github.com/qingjian-team/qingjian) 进行深度扩展与俄语专版定制；
- 代码部分采用 [GPL-3.0-or-later](LICENSE) 协议开源；
- 俄语词库数据遵循 [MIT](LICENSE) / 开源词典衍生授权协议。
