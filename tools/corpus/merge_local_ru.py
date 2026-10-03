# /// script
# requires-python = ">=3.11"
# dependencies = ["opencc-python-reimplemented"]
# ///
"""把本地俄汉词典 `dict_full.json` 清洗合并进 `assets/glossary/glossary-ru.tsv`（ORD-006）。

规则（ORD-006 规格，与 `glossary_ru.py::verify_table` 的门禁常量对齐）：
  * `cn` 经 OpenCC `t2s` 转简体，只收纯汉字词条；
  * `plain` 取俄语原形、转小写、压缩内部空白；须匹配西里尔正则（`[\\u0400-\\u04FF\\u0301 -]`）、
    至少含一个西里尔字母、<= 40 字符、<= 4 词；
  * 词性映射：含 verb→`v.` / adj→`adj.` / adv→`adv.` / 其余（含缺省与 noun）→`n.`；
  * 现有种子表优先级最高（同名释义排在最前），新释义去重后追加，单个词条最多 5 条释义；
  * 输出 UTF-8 无 BOM、LF 换行，首列按 Unicode 码点严格递增、无重复。

用法：
    python tools/corpus/merge_local_ru.py            # 用默认源/目标执行
    python tools/corpus/merge_local_ru.py --dry-run  # 只统计不写文件
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from opencc import OpenCC

DEFAULT_SRC = Path(r"C:\Users\32940\WorkBuddy\俄语背单词软件\dict_full.json")
DEFAULT_TARGET = Path("assets/glossary/glossary-ru.tsv")

# 门禁 `glossary_ru.py` 的同一套常量
CYRILLIC_PATTERN = re.compile(r"^[\u0400-\u04FF\u0301 -]+$")
CYRILLIC_LETTER = re.compile(r"[\u0400-\u04FF]")
CJK_PATTERN = re.compile(r"^[\u4e00-\u9fa5]+$")
MAX_CHARS = 40
MAX_WORDS = 4
MAX_SENSES_PER_WORD = 5


def pos_tag(raw: str) -> str:
    """`pos` 字段 → 青简允许的词性标签。"""
    text = (raw or "").lower()
    if "verb" in text:
        return "v."
    if "adj" in text:
        return "adj."
    if "adv" in text:
        return "adv."
    return "n."


def load_existing(target: Path) -> tuple[str | None, dict[str, list[str]]]:
    """读回已有表（含表头注释），种子词条原样保留。"""
    header: str | None = None
    glossary: dict[str, list[str]] = {}
    if not target.is_file():
        return header, glossary
    for line in target.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        if line.startswith("#"):
            if header is None:
                header = line
            continue
        parts = line.split("\t")
        word = parts[0].strip()
        if word:
            glossary[word] = [s.strip() for s in parts[1:] if s.strip()]
    return header, glossary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", default=str(DEFAULT_SRC), help="源 JSON")
    parser.add_argument("--target", default=str(DEFAULT_TARGET), help="目标 TSV")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写文件")
    args = parser.parse_args()

    src = Path(args.src)
    target = Path(args.target)
    if not src.is_file():
        print(f"源文件不存在：{src}", file=sys.stderr)
        return 1

    converter = OpenCC("t2s")
    header, glossary = load_existing(target)
    seed_count = len(glossary)

    with src.open(encoding="utf-8") as handle:
        records = json.load(handle)

    added_words = 0
    added_senses = 0
    skipped = 0
    for item in records:
        cn = converter.convert((item.get("cn") or "").strip()).strip()
        plain = " ".join((item.get("plain") or "").split()).lower()
        if not cn or not CJK_PATTERN.match(cn):
            skipped += 1
            continue
        if not plain or not CYRILLIC_PATTERN.match(plain) or not CYRILLIC_LETTER.search(plain):
            skipped += 1
            continue
        if len(plain) > MAX_CHARS or len(plain.split()) > MAX_WORDS:
            skipped += 1
            continue

        gloss = f"{pos_tag(item.get('pos', ''))} {plain}"
        bucket = glossary.get(cn)
        if bucket is None:
            glossary[cn] = [gloss]
            added_words += 1
            added_senses += 1
        elif gloss not in bucket and len(bucket) < MAX_SENSES_PER_WORD:
            bucket.append(gloss)
            added_senses += 1
        else:
            skipped += 1

    words = sorted(glossary)
    lines = [header] if header else []
    for word in words:
        senses = glossary[word]
        if senses:
            lines.append("\t".join([word] + senses))
    payload = ("\n".join(lines) + "\n").encode("utf-8")

    print(f"种子词条 {seed_count} 条 | 新增词 {added_words} | 新增释义 {added_senses} | 跳过 {skipped}")
    print(f"输出总词条 {len(words)} | 字节 {len(payload)} | 表头 {'保留' if header else '无'}")

    if args.dry_run:
        print("（dry-run，未写文件）")
        return 0

    target.write_bytes(payload)
    print(f"已写入：{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
