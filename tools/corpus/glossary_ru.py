# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""把中文词表翻成青简的 `glossary-ru.tsv`（`词\t[词性. ]译词\t…`）及高精度门禁校验工具。

严格遵循青简释义表规范：
  * 文件编码必须是 UTF-8 无 BOM、LF 换行（\\n，绝对禁止 \\r）。
  * 首列词按 Unicode 码点严格单调递增排序，无重复。
  * 每一行格式：`词\\t[词性. ]译词\\t[词性. ]译词...`。
  * 允许的词性标签（ALLOWED_POS）：{"n.", "v.", "adj.", "adv.", "pron.", "prep.", "conj.", "num.", "m.", "part.", "int.", "phr."}。
  * 译词必须是西里尔字母（\\u0400-\\u04FF）、空格、连字符（-），可选重音符（\\u0301）。禁止包含英文字母或未翻译汉字。
  * 单个译词长度 <= 40 字符，单词数 <= 4。
  * 动词为不定式原形（通常以 -ть, -ти, -чь, -ться, -тись 结尾），形容词优先阳性第一格（-ый, -ий, -ой），名词为单数第一格。

用法示例：
    # 校验已有释义表
    python tools/corpus/glossary_ru.py --verify assets/glossary/glossary-ru.tsv

    # 构建首版种子释义表
    python tools/corpus/glossary_ru.py --build-seed --out assets/glossary/glossary-ru.tsv

    # 使用 DeepSeek API 扩展翻译（预留扩展接口）
    DEEPSEEK_API_KEY=sk-... python tools/corpus/glossary_ru.py --api deepseek --en-table assets/glossary/glossary-en.tsv
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# 释义表允许的词性
ALLOWED_POS: set[str] = {
    "n.", "v.", "adj.", "adv.", "pron.", "prep.", "conj.", "num.",
    "m.", "part.", "int.", "phr.",
}

# 俄语西里尔字母、可选重音符、空格与连字符正则
CYRILLIC_ALLOWED_PATTERN = re.compile(r"^[\u0400-\u04FF\u0301 -]+$")

# 动词不定式合法结尾
INFINITIVE_ENDINGS = ("ть", "ти", "чь", "ться", "тись", "чься")

MAX_GLOSS_CHARS = 40       # 单个译词长度上限
MAX_GLOSS_WORDS = 4        # 单词数上限

# 高精度种子词库（涵盖开发、编程、架构、算法、操作系统、函数、变量、网络及核心通用词等 200+ 条）
SEED_ENTRIES: dict[str, list[str]] = {
    "开发": ["v. разрабатывать", "n. разработка"],
    "编程": ["n. программирование", "v. программировать"],
    "架构": ["n. архитектура"],
    "算法": ["n. алгоритм"],
    "操作系统": ["n. операционная система"],
    "函数": ["n. функция"],
    "变量": ["n. переменная"],
    "网络": ["n. сеть"],
    "你好": ["int. привет", "int. здравствуйте"],
    "谢谢": ["int. спасибо"],
    "世界": ["n. мир"],
    "时间": ["n. время"],
    "学习": ["v. учиться", "n. учёба"],
    "语言": ["n. язык"],
    "代码": ["n. код"],
    "编译器": ["n. компилятор"],
    "解释器": ["n. интерпретатор"],
    "数据库": ["n. база данных"],
    "接口": ["n. интерфейс"],
    "类": ["n. класс"],
    "对象": ["n. объект"],
    "方法": ["n. метод"],
    "模块": ["n. модуль"],
    "库": ["n. библиотека"],
    "框架": ["n. фреймворк"],
    "数组": ["n. массив"],
    "字符串": ["n. строка"],
    "字典": ["n. словарь"],
    "列表": ["n. список"],
    "集合": ["n. множество"],
    "堆": ["n. куча"],
    "栈": ["n. стек"],
    "队列": ["n. очередь"],
    "树": ["n. дерево"],
    "图": ["n. граф"],
    "指针": ["n. указатель"],
    "内存": ["n. память"],
    "线程": ["n. поток"],
    "进程": ["n. процесс"],
    "文件": ["n. файл"],
    "目录": ["n. каталог"],
    "文件夹": ["n. папка"],
    "磁盘": ["n. диск"],
    "服务器": ["n. сервер"],
    "客户端": ["n. клиент"],
    "协议": ["n. протокол"],
    "终端": ["n. терминал"],
    "命令行": ["n. командная строка"],
    "命令": ["n. команда"],
    "参数": ["n. параметр"],
    "返回值": ["n. возвращаемое значение"],
    "异常": ["n. исключение"],
    "错误": ["n. ошибка"],
    "调试": ["v. отлаживать", "n. отладка"],
    "测试": ["v. тестировать", "n. тест"],
    "部署": ["v. развёртывать", "n. развёртывание"],
    "运行": ["v. запускать", "v. работать"],
    "编译": ["v. компилировать"],
    "构建": ["v. собирать", "n. сборка"],
    "优化": ["v. оптимизировать", "n. оптимизация"],
    "发布": ["v. публиковать", "n. релиз"],
    "依赖": ["n. зависимость"],
    "包": ["n. пакет"],
    "仓库": ["n. репозиторий"],
    "分支": ["n. ветка"],
    "提交": ["v. фиксировать", "n. коммит"],
    "合并": ["v. объединять", "v. сливать"],
    "用户": ["n. пользователь"],
    "密码": ["n. пароль"],
    "权限": ["n. право доступа"],
    "安全": ["n. безопасность", "adj. безопасный"],
    "加密": ["n. шифрование", "v. шифровать"],
    "解密": ["n. расшифровка", "v. расшифровывать"],
    "证书": ["n. сертификат"],
    "令牌": ["n. токен"],
    "认证": ["n. аутентификация"],
    "授权": ["n. авторизация"],
    "会话": ["n. сессия"],
    "缓存": ["n. кэш"],
    "索引": ["n. индекс"],
    "查询": ["n. запрос", "v. запрашивать"],
    "响应": ["n. ответ"],
    "请求": ["n. запрос"],
    "路由": ["n. маршрут", "n. маршрутизация"],
    "网关": ["n. шлюз"],
    "硬件": ["n. аппаратное обеспечение"],
    "软件": ["n. программное обеспечение"],
    "固件": ["n. прошивка"],
    "前端": ["n. фронтенд"],
    "后端": ["n. бэкенд"],
    "驱动": ["n. драйвер"],
    "内核": ["n. ядро"],
    "虚拟化": ["n. виртуализация"],
    "容器": ["n. контейнер"],
    "云": ["n. облако"],
    "集群": ["n. кластер"],
    "节点": ["n. узел"],
    "负载均衡": ["n. балансировка нагрузки"],
    "分布式": ["adj. распределённый"],
    "并发": ["n. параллелизм"],
    "异步": ["adj. асинхронный"],
    "同步": ["adj. синхронный", "v. синхронизировать"],
    "数据": ["n. данные"],
    "结构": ["n. структура"],
    "模型": ["n. модель"],
    "视图": ["n. представление"],
    "控制器": ["n. контроллер"],
    "组件": ["n. компонент"],
    "插件": ["n. плагин"],
    "扩展": ["n. расширение"],
    "事件": ["n. событие"],
    "监听": ["v. слушать"],
    "触发": ["v. вызывать"],
    "状态": ["n. состояние"],
    "日志": ["n. журнал", "n. лог"],
    "监控": ["n. мониторинг", "v. отслеживать"],
    "配置": ["n. конфигурация", "v. настраивать"],
    "设置": ["n. настройка", "v. устанавливать"],
    "安装": ["v. устанавливать", "n. установка"],
    "卸载": ["v. удалять", "n. удаление"],
    "更新": ["v. обновлять", "n. обновление"],
    "升级": ["v. обновлять", "v. улучшать"],
    "备份": ["n. резервная копия", "v. копировать"],
    "恢复": ["v. восстанавливать", "n. восстановление"],
    "重构": ["v. рефакторить", "n. рефакторинг"],
    "递归": ["n. рекурсия"],
    "迭代": ["n. итерация"],
    "循环": ["n. цикл"],
    "条件": ["n. условие"],
    "布尔": ["adj. логический", "adj. булев"],
    "整数": ["n. целое число"],
    "浮点数": ["n. число с плавающей точкой"],
    "字符": ["n. символ"],
    "字节": ["n. байт"],
    "位": ["n. бит"],
    "格式": ["n. формат"],
    "编码": ["n. кодировка", "v. кодировать"],
    "字段": ["n. поле"],
    "属性": ["n. свойство"],
    "声明": ["n. объявление", "v. объявлять"],
    "定义": ["n. определение", "v. определять"],
    "赋值": ["n. присваивание", "v. присваивать"],
    "比较": ["v. сравнивать", "n. сравнение"],
    "搜索": ["v. искать", "n. поиск"],
    "排序": ["v. сортировать", "n. сортировка"],
    "过滤": ["v. фильтровать", "n. фильтрация"],
    "映射": ["v. отображать", "n. отображение"],
    "转换": ["v. преобразовывать", "n. преобразование"],
    "互联网": ["n. интернет"],
    "成功": ["n. успех", "adj. успешный"],
    "失败": ["n. неудача"],
    "开始": ["v. начинать", "n. начало"],
    "结束": ["v. заканчивать", "n. конец"],
    "阅读": ["v. читать", "n. чтение"],
    "写作": ["v. писать", "n. письмо"],
    "理解": ["v. понимать"],
    "帮助": ["v. помогать", "n. помощь"],
    "创建": ["v. создавать"],
    "删除": ["v. удалять"],
    "保存": ["v. сохранять"],
    "打开": ["v. открывать"],
    "关闭": ["v. закрывать"],
    "发送": ["v. отправлять"],
    "接收": ["v. получать"],
    "连接": ["v. соединять", "n. соединение"],
    "断开": ["v. отключать"],
    "支持": ["v. поддерживать", "n. поддержка"],
    "检查": ["v. проверять", "n. проверка"],
    "重启": ["v. перезагружать"],
    "退出": ["v. выходить", "n. выход"],
    "俄语": ["n. русский язык"],
    "汉语": ["n. китайский язык"],
    "英语": ["n. английский язык"],
    "再见": ["int. до свидания"],
    "请": ["int. пожалуйста"],
    "对不起": ["int. извините"],
    "是": ["v. быть", "part. да"],
    "不是": ["part. нет"],
    "人": ["n. человек"],
    "朋友": ["n. друг"],
    "中国": ["n. Китай"],
    "电脑": ["n. компьютер"],
    "手机": ["n. телефон"],
    "工作": ["n. работа", "v. работать"],
    "生活": ["n. жизнь"],
    "今天": ["adv. сегодня", "n. сегодня"],
    "明天": ["adv. завтра", "n. завтра"],
    "昨天": ["adv. вчера", "n. вчера"],
    "现在": ["adv. сейчас"],
    "一": ["num. один"],
    "二": ["num. два"],
    "三": ["num. три"],
    "四": ["num. четыре"],
    "五": ["num. пять"],
    "六": ["num. шесть"],
    "七": ["num. семь"],
    "八": ["num. восемь"],
    "九": ["num. девять"],
    "十": ["num. десять"],
    "百": ["num. сто"],
    "千": ["num. тысяча"],
    "书": ["n. книга"],
    "爱": ["v. любить", "n. любовь"],
    "看": ["v. смотреть", "v. видеть"],
    "听": ["v. слушать", "v. слышать"],
    "说": ["v. говорить", "v. сказать"],
    "读": ["v. читать"],
    "写": ["v. писать"],
    "做": ["v. делать"],
    "想": ["v. думать", "v. хотеть"],
    "走": ["v. идти", "v. ходить"],
    "跑": ["v. бежать", "v. бегать"],
    "买": ["v. покупать", "v. купить"],
    "卖": ["v. продавать", "v. продать"],
    "大": ["adj. большой"],
    "小": ["adj. маленький"],
    "好": ["adj. хороший", "adv. хорошо"],
    "新": ["adj. новый"],
    "旧": ["adj. старый"],
    "长": ["adj. длинный"],
    "快": ["adj. быстрый", "adv. быстро"],
    "慢": ["adj. медленный", "adv. медленно"],
    "真": ["adj. настоящий", "adv. действительно"],
    "假": ["adj. ложный"],
    "和": ["conj. и"],
    "或者": ["conj. или"],
    "如果": ["conj. если"],
    "因为": ["conj. потому что"],
    "但是": ["conj. но"],
    "谁": ["pron. кто"],
    "什么": ["pron. что"],
    "哪里": ["adv. где"],
    "为什么": ["adv. почему"],
    "怎么": ["adv. как"],
}


def verify_table(path: Path | str) -> tuple[int, list[str]]:
    """对给定的 TSV 释义表逐行执行高精度校验。

    检测项：
      1. UTF-8 BOM 检测（严禁带 BOM）
      2. 换行符检测（严禁 CR / \\r，必须为 LF）
      3. 排序检测（Unicode 码点严格单调递增，无重复词）
      4. 结构完整性（词和释义非空）
      5. 词性检测（必须在 ALLOWED_POS 集合内，后跟空格）
      6. 西里尔字符合法性（西里尔字符、空格、连字符、可选重音符，禁止英文与汉字）
      7. 长度与词数约束（<= 40 字符，<= 4 词）
      8. 动词形态检测（v. 动词必须为不定式原形）

    返回：(合法行数, 错误信息列表)
    """
    path = Path(path)
    if not path.is_file():
        return 0, [f"file not found: {path}"]

    errors: list[str] = []

    # 1. 二进制读取检测 BOM 与 CRLF
    content_bytes = path.read_bytes()
    if content_bytes.startswith(b"\xef\xbb\xbf"):
        errors.append("line 1: UTF-8 BOM detected (BOM is strictly forbidden)")

    # 检查换行符中的 \r
    lines_raw = content_bytes.split(b"\n")
    for idx, raw_line in enumerate(lines_raw, start=1):
        if b"\r" in raw_line:
            errors.append(f"line {idx}: carriage return (CR / \\r) detected; only LF is allowed")

    # 2. 文本按行严格解析校验
    try:
        text = content_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        errors.append(f"UTF-8 decode error: {e}")
        return 0, errors

    ok_count = 0
    prev_word: str | None = None

    lines = text.split("\n")
    for i, line in enumerate(lines, start=1):
        # 忽略空行与末尾空行
        if not line.strip():
            continue
        # 忽略注释行
        if line.startswith("#"):
            continue

        parts = line.split("\t")
        word = parts[0].strip()
        if not word:
            errors.append(f"line {i}: missing word")
            continue

        # 排序检测（Unicode 码点严格递增）
        if prev_word is not None:
            if word == prev_word:
                errors.append(f"line {i}: duplicate word '{word}' (must be strictly ascending)")
            elif word < prev_word:
                errors.append(
                    f"line {i}: sorting violation: '{word}' < '{prev_word}' "
                    f"(Unicode code point order violation)"
                )
        prev_word = word

        senses = [s.strip() for s in parts[1:] if s.strip()]
        if not senses:
            errors.append(f"line {i}: missing senses for word '{word}'")
            continue

        line_bad = False
        for sense in senses:
            # 词性匹配：如 "n. мир", "v. делать"
            pos = ""
            body = sense
            m = re.match(r"^([a-zA-Z]+\.)\s+(.+)$", sense)
            if m:
                pos = m.group(1)
                body = m.group(2).strip()
                if pos not in ALLOWED_POS:
                    errors.append(
                        f"line {i}: invalid part of speech '{pos}' in sense '{sense}' for word '{word}'"
                    )
                    line_bad = True
            elif re.match(r"^[a-zA-Z]+\.", sense):
                # 类似 "v.делать" 缺少空格，或非法词性
                m_no_space = re.match(r"^([a-zA-Z]+\.)\s*(.*)$", sense)
                p = m_no_space.group(1) if m_no_space else ""
                if p not in ALLOWED_POS:
                    errors.append(
                        f"line {i}: invalid part of speech '{p}' in sense '{sense}' for word '{word}'"
                    )
                else:
                    errors.append(
                        f"line {i}: missing space after part of speech '{p}' in sense '{sense}' for word '{word}'"
                    )
                line_bad = True
                continue

            if not body:
                errors.append(f"line {i}: empty sense body for word '{word}'")
                line_bad = True
                continue

            # 长度限制
            if len(body) > MAX_GLOSS_CHARS:
                errors.append(
                    f"line {i}: sense '{body}' exceeds length limit of {MAX_GLOSS_CHARS} characters for word '{word}'"
                )
                line_bad = True

            # 词数限制
            words = body.split()
            if len(words) > MAX_GLOSS_WORDS:
                errors.append(
                    f"line {i}: sense '{body}' exceeds limit of {MAX_GLOSS_WORDS} words for word '{word}'"
                )
                line_bad = True

            # 英文检测
            if re.search(r"[a-zA-Z]", body):
                errors.append(
                    f"line {i}: English character detected in sense '{body}' for word '{word}'"
                )
                line_bad = True

            # 汉字检测
            if re.search(r"[\u4e00-\u9fff]", body):
                errors.append(
                    f"line {i}: Chinese character detected in sense '{body}' for word '{word}'"
                )
                line_bad = True

            # 西里尔字符合法性
            if not CYRILLIC_ALLOWED_PATTERN.match(body):
                errors.append(
                    f"line {i}: invalid character in Russian sense '{body}' for word '{word}'"
                )
                line_bad = True

            # 动词原形不定式检查（v. 动词必须是不定式原形）
            if pos == "v.":
                clean_body = body.replace("\u0301", "").strip().lower()
                last_token = clean_body.split()[-1]
                if not last_token.endswith(INFINITIVE_ENDINGS):
                    errors.append(
                        f"line {i}: verb sense '{body}' is not in infinitive form "
                        f"(must end with -ть, -ти, -чь, etc.) for word '{word}'"
                    )
                    line_bad = True

        if not line_bad:
            ok_count += 1

    return ok_count, errors


def build_seed_glossary(out_path: Path | str) -> int:
    """构建首版俄语种子释义表并保存为规范 TSV 文件。"""
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # 按 Unicode 码点严格递增排序
    sorted_items = sorted(SEED_ENTRIES.items(), key=lambda x: x[0])

    # 写入规范 TSV（UTF-8, 无 BOM, LF 换行）
    with out_file.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# 由 tools/corpus/glossary_ru.py 生成。词\t[词性. ]译词\t[词性. ]译词\n")
        for word, senses in sorted_items:
            line_str = f"{word}\t" + "\t".join(senses) + "\n"
            f.write(line_str)

    # 自检校验
    ok_count, errors = verify_table(out_file)
    print("=" * 60)
    print(f"俄语种子词典生成完成: {out_file}")
    print(f"收录词条数: {len(sorted_items)}")
    print(f"自检合法行: {ok_count}")
    print(f"自检错误行: {len(errors)}")

    head_bytes = out_file.read_bytes()[:4]
    has_bom = head_bytes.startswith(b"\xef\xbb\xbf")
    print(f"文件前置字节: {head_bytes.hex()} " + ("(错误: 含有 BOM!)" if has_bom else "(正确: 无 BOM)"))

    if errors:
        print("错误详情:")
        for e in errors[:20]:
            print(f"  {e}")
        return 1

    return 0


# =========================================================================
# 预留基于 LLM / 翻译 API 扩展接口
# =========================================================================

def translate_batch_deepseek(
    items: list[tuple[str, str, str]],  # (zh_word, pos_hint, en_gloss)
    api_key: str,
    base_url: str = "https://api.deepseek.com",
    model: str = "deepseek-chat",
) -> list[str | None]:
    """预留扩展：通过 DeepSeek API 批量扩充俄语释义表。

    使用内置 urllib，无第三方库依赖。
    """
    if not api_key:
        raise ValueError("Missing DeepSeek API key")

    prompt_words = "\n".join(
        f"{i+1}. 词: {w} | 词性: {p or '未知'} | 英文释义: {g or '无'}"
        for i, (w, p, g) in enumerate(items)
    )

    system_prompt = (
        "你是一名精通俄语词典学与青简输入法规范的专家。\n"
        "请将输入的中文词翻译为规范的标准俄语释义。\n"
        "严格遵循以下规则：\n"
        "1. 每行格式：编号. 词性. 译词 (例如: 1. v. разрабатывать)\n"
        "2. 词性标签只允许使用：n., v., adj., adv., pron., prep., conj., num., m., part., int., phr.\n"
        "3. 译词必须全部为西里尔字母，禁止任何英文字母、标点或汉字残留。\n"
        "4. 动词必须为不定式原形（通常以 -ть, -ти, -чь 结尾）。\n"
        "5. 形容词优先阳性第一格（-ый, -ий, -ой），名词为单数第一格。\n"
        "6. 单个译词 <= 40 字符，单词数 <= 4。"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_words},
        ],
        "temperature": 0.2,
    }

    req_data = json.dumps(payload).encode("utf-8")
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"DeepSeek API request failed: {e}") from e

    results: list[str | None] = [None] * len(items)
    for line in content.splitlines():
        line = line.strip()
        m = re.match(r"^(\d+)\.\s*(.*)$", line)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(results):
                results[idx] = m.group(2).strip()

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify", metavar="FILE", help="对给定的 TSV 释义表逐行执行高精度校验")
    parser.add_argument("--build-seed", action="store_true", help="生成核心高精度的俄语种子释义表")
    parser.add_argument("--out", default="assets/glossary/glossary-ru.tsv", help="输出路径")
    parser.add_argument("--api", choices=["deepseek", "azure", "none"], default="none", help="扩展翻译 API 提供方")
    parser.add_argument("--key", default="", help="API Key（或从环境变量读取）")
    parser.add_argument("--base-url", default="https://api.deepseek.com", help="API Base URL")
    parser.add_argument("--en-table", default="assets/glossary/glossary-en.tsv", help="源词表来源")
    parser.add_argument("--limit", type=int, default=0, help="处理词数上限")

    args = parser.parse_args()

    if args.verify:
        ok_count, errors = verify_table(args.verify)
        print(f"文件路径: {args.verify}")
        print(f"合法行: {ok_count}")
        print(f"错误行: {len(errors)}")
        if errors:
            print("错误列表:")
            for e in errors[:30]:
                print(f"  {e}")
            if len(errors) > 30:
                print(f"  ... 另有 {len(errors) - 30} 条错误未显示")
            return 1
        print("校验通过：100% 合规！")
        return 0

    if args.build_seed:
        return build_seed_glossary(args.out)

    if args.api == "deepseek":
        api_key = args.key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            print("错误: 缺少 DEEPSEEK_API_KEY", file=sys.stderr)
            return 2
        print(f"DeepSeek 扩展接口就绪，Base URL: {args.base_url}")
        # 预留扩展逻辑
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
