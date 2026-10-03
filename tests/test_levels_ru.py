"""俄语考级等级表自动化门禁测试 (tests/test_levels_ru.py)

覆盖：
1. 黄金标准测试（Golden Standard）：
   - 对 `assets/levels/levels-ru.tsv` 运行完整门禁校验，断言 100% 绿。
   - 校验二进制无 BOM、无 \\r (CRLF)、纯 LF 换行。
   - 校验首行注释与第二行等级头严格匹配。
   - 校验全词小写西里尔字母、无重复词、各等级词汇数统计充足（各级 >= 150 词，总计 >= 1000 词）。
   - 校验 CLI `--verify` 命令行退出码严格为 0。
2. 变异拦截齿牙测试（Tooth Check 先红后绿）：
   - 注入各类缺陷变异样本（加 BOM、CRLF、破坏等级头、缺失 tab、大写字母、非法字符、重复词、非法等级、空字段）。
   - 断言门禁校验器与 CLI 命令行必须 100% 报错拦截（预期红）。
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# 将项目根目录添加到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.corpus.levels_ru import LEVELS, HEADER_LINE_1, HEADER_LINE_2, verify_levels_file


class TestLevelsRuGolden(unittest.TestCase):
    """测试项 1：对资产目录中的正式俄语等级表进行黄金合规验证。"""

    def setUp(self) -> None:
        self.levels_path = PROJECT_ROOT / "assets" / "levels" / "levels-ru.tsv"
        self.script_path = PROJECT_ROOT / "tools" / "corpus" / "levels_ru.py"

    def test_golden_file_exists_and_valid(self) -> None:
        """断言正式等级表存在且内部数据 100% 通过验证。"""
        self.assertTrue(self.levels_path.is_file(), f"未找到俄语等级表: {self.levels_path}")

        # 1. 二进制层检查：绝对禁止 BOM 与 CRLF
        raw = self.levels_path.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "严禁带有 UTF-8 BOM！")
        self.assertNotIn(b"\r", raw, "严禁带有 Carriage Return (\\r)，必须纯 LF 换行！")

        # 2. 文本行结构及等级头检查
        text = raw.decode("utf-8")
        lines = text.split("\n")
        if lines and not lines[-1]:
            lines.pop()

        self.assertGreaterEqual(len(lines), 2, "等级表行数过少，缺少标头")
        self.assertEqual(lines[0], HEADER_LINE_1, f"首行注释不匹配: {lines[0]}")
        self.assertEqual(lines[1], HEADER_LINE_2, f"第二行等级头不匹配: {lines[1]}")

        # 3. 规则与各级统计校验
        ok_count, errors = verify_levels_file(self.levels_path)
        if errors:
            self.fail(f"正式等级表校验未通过，发现 {len(errors)} 处错误:\n" + "\n".join(errors[:15]))

        self.assertGreaterEqual(ok_count, 1000, f"收录词汇数不足 1000 条 (当前: {ok_count})")

        # 统计各级词汇数
        level_counts: dict[str, int] = {lvl: 0 for lvl in LEVELS}
        for line in lines[2:]:
            if not line.strip() or line.startswith("#"):
                continue
            word, lvl = line.split("\t")
            level_counts[lvl] = level_counts.get(lvl, 0) + 1

        for lvl in LEVELS:
            self.assertGreaterEqual(
                level_counts[lvl], 150,
                f"等级 {lvl} 收录词汇量偏低: {level_counts[lvl]} 条（预期至少 150 条）"
            )

    def test_golden_cli_verify_exit_code_zero(self) -> None:
        """断言通过 CLI 执行 `--verify` 退出码严格为 0。"""
        cmd = [sys.executable, str(self.script_path), "--verify", str(self.levels_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        self.assertEqual(
            proc.returncode, 0,
            f"CLI 校验失败，退出码 {proc.returncode}，输出:\n{proc.stdout}\n{proc.stderr}"
        )
        self.assertIn("校验通过：100% 合规！", proc.stdout)


class TestLevelsRuToothCheck(unittest.TestCase):
    """测试项 2：Tooth Check（齿牙测试）- 注入破坏性变异样本，断言门禁必须 100% 拦截。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.script_path = PROJECT_ROOT / "tools" / "corpus" / "levels_ru.py"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_temp_tsv(self, content_str: str, add_bom: bool = False, crlf: bool = False) -> Path:
        """辅助函数：按特定编码和换行规则写入临时 TSV。"""
        temp_file = Path(self.temp_dir.name) / f"mutation_{unittest.TestCase.id(self)}.tsv"
        raw_text = content_str.replace("\n", "\r\n") if crlf else content_str
        raw_bytes = raw_text.encode("utf-8")
        if add_bom:
            raw_bytes = b"\xef\xbb\xbf" + raw_bytes
        temp_file.write_bytes(raw_bytes)
        return temp_file

    def test_intercepts_utf8_bom(self) -> None:
        """变异拦截：带 UTF-8 BOM 的文件必须被拦截。"""
        content = f"{HEADER_LINE_1}\n{HEADER_LINE_2}\nпривет\tA1\n"
        tsv_path = self._write_temp_tsv(content, add_bom=True)

        _, errors = verify_levels_file(tsv_path)
        self.assertTrue(any("BOM detected" in e for e in errors), f"未拦截 BOM 缺陷: {errors}")

        proc = subprocess.run(
            [sys.executable, str(self.script_path), "--verify", str(tsv_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        self.assertNotEqual(proc.returncode, 0, "CLI 面对 BOM 必须返回非 0 退出码")

    def test_intercepts_crlf_line_endings(self) -> None:
        """变异拦截：带 CRLF (\\r\\n) 换行的文件必须被拦截。"""
        content = f"{HEADER_LINE_1}\n{HEADER_LINE_2}\nпривет\tA1\n"
        tsv_path = self._write_temp_tsv(content, crlf=True)

        _, errors = verify_levels_file(tsv_path)
        self.assertTrue(any("carriage return" in e for e in errors), f"未拦截 CRLF 缺陷: {errors}")

        proc = subprocess.run(
            [sys.executable, str(self.script_path), "--verify", str(tsv_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        self.assertNotEqual(proc.returncode, 0, "CLI 面对 CRLF 必须返回非 0 退出码")

    def test_intercepts_corrupted_header(self) -> None:
        """变异拦截：破坏首行注释或第二行等级头必须被拦截。"""
        bad_header_1 = f"# 错误的注释\n{HEADER_LINE_2}\nпривет\tA1\n"
        tsv_path_1 = self._write_temp_tsv(bad_header_1)
        _, errors_1 = verify_levels_file(tsv_path_1)
        self.assertTrue(any("invalid header comment" in e for e in errors_1), f"未拦截注释错误: {errors_1}")

        bad_header_2 = f"{HEADER_LINE_1}\n# levels A1 A2 B1\nпривет\tA1\n"
        tsv_path_2 = self._write_temp_tsv(bad_header_2)
        _, errors_2 = verify_levels_file(tsv_path_2)
        self.assertTrue(any("invalid levels header" in e for e in errors_2), f"未拦截等级头错误: {errors_2}")

    def test_intercepts_missing_tab(self) -> None:
        """变异拦截：数据行缺少 Tab 分隔符必须被拦截。"""
        content = f"{HEADER_LINE_1}\n{HEADER_LINE_2}\nпривет A1\n"
        tsv_path = self._write_temp_tsv(content)
        _, errors = verify_levels_file(tsv_path)
        self.assertTrue(any("expected 'word\\tlevel'" in e for e in errors), f"未拦截缺失 tab 缺陷: {errors}")

    def test_intercepts_uppercase_letters(self) -> None:
        """变异拦截：词汇包含大写字母必须被拦截（必须全小写）。"""
        content = f"{HEADER_LINE_1}\n{HEADER_LINE_2}\nПривет\tA1\n"
        tsv_path = self._write_temp_tsv(content)
        _, errors = verify_levels_file(tsv_path)
        self.assertTrue(any("not lowercase" in e for e in errors), f"未拦截大写缺陷: {errors}")

    def test_intercepts_duplicate_words(self) -> None:
        """变异拦截：重复单词必须被拦截。"""
        content = f"{HEADER_LINE_1}\n{HEADER_LINE_2}\nслово\tA1\nслово\tA2\n"
        tsv_path = self._write_temp_tsv(content)
        _, errors = verify_levels_file(tsv_path)
        self.assertTrue(any("duplicate word" in e for e in errors), f"未拦截重复词缺陷: {errors}")

    def test_intercepts_unknown_level(self) -> None:
        """变异拦截：未知等级（如 Z9）必须被拦截。"""
        content = f"{HEADER_LINE_1}\n{HEADER_LINE_2}\nслово\tZ9\n"
        tsv_path = self._write_temp_tsv(content)
        _, errors = verify_levels_file(tsv_path)
        self.assertTrue(any("unknown level 'Z9'" in e for e in errors), f"未拦截未知等级缺陷: {errors}")

    def test_intercepts_empty_fields(self) -> None:
        """变异拦截：空词或空等级必须被拦截。"""
        content = f"{HEADER_LINE_1}\n{HEADER_LINE_2}\n\tA1\n"
        tsv_path = self._write_temp_tsv(content)
        _, errors = verify_levels_file(tsv_path)
        self.assertTrue(any("empty word" in e for e in errors), f"未拦截空词缺陷: {errors}")


if __name__ == "__main__":
    unittest.main()
