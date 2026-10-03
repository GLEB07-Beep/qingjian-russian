"""俄语释义表与门禁校验自动化测试 (tests/test_glossary_ru.py)

覆盖：
1. 黄金标准测试（Golden Standard）：
   - 对 `assets/glossary/glossary-ru.tsv` 运行完整高精度校验，断言 100% 绿。
   - 校验二进制无 BOM、无 \\r (CRLF)、严格单调递增排序、西里尔字符合法性、动词原形等。
2. 变异拦截齿牙测试（Tooth Check 先红后绿）：
   - 故意注入破坏性缺陷变异样本（加 BOM、CRLF、非法词性、英语混入、汉字混入、顺序颠倒、重复词、超长译词、超词数、非不定式动词、缺失释义）。
   - 断言门禁高精度校验器与 CLI 命令行必须 100% 报错拦截（预期红）。
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

from tools.corpus.glossary_ru import verify_table


class TestGlossaryRuGolden(unittest.TestCase):
    """测试项 1：对资产目录中的正式俄语释义表进行黄金合规验证。"""

    def setUp(self) -> None:
        self.glossary_path = PROJECT_ROOT / "assets" / "glossary" / "glossary-ru.tsv"
        self.script_path = PROJECT_ROOT / "tools" / "corpus" / "glossary_ru.py"

    def test_golden_file_exists_and_valid(self) -> None:
        """断言正式表存在且内部数据 100% 通过验证。"""
        self.assertTrue(self.glossary_path.is_file(), f"未找到释义表: {self.glossary_path}")

        # 1. 二进制层检查
        raw = self.glossary_path.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "严禁带有 UTF-8 BOM！")
        self.assertNotIn(b"\r", raw, "严禁带有 Carriage Return (\\r)，必须纯 LF 换行！")

        # 2. 规则校验
        ok_count, errors = verify_table(self.glossary_path)
        if errors:
            self.fail(f"正式释义表校验未通过，发现 {len(errors)} 处错误:\n" + "\n".join(errors[:10]))
        self.assertGreaterEqual(ok_count, 100, f"种子释义表词条数不足 100 (当前: {ok_count})")

    def test_golden_cli_verify_exit_code_zero(self) -> None:
        """断言通过 CLI 执行 `--verify` 退出码严格为 0。"""
        cmd = [sys.executable, str(self.script_path), "--verify", str(self.glossary_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        self.assertEqual(
            proc.returncode, 0,
            f"CLI 校验失败，退出码 {proc.returncode}，输出:\n{proc.stdout}\n{proc.stderr}"
        )
        self.assertIn("校验通过：100% 合规！", proc.stdout)


class TestGlossaryRuToothCheck(unittest.TestCase):
    """测试项 2：Tooth Check（齿牙测试）- 注入破坏性变异样本，断言门禁必须拦截。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.script_path = PROJECT_ROOT / "tools" / "corpus" / "glossary_ru.py"

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
        valid_content = "你好\tint. привет\n世界\tn. мир\n"
        tsv_path = self._write_temp_tsv(valid_content, add_bom=True)

        _, errors = verify_table(tsv_path)
        self.assertTrue(any("BOM detected" in e for e in errors), f"未拦截 BOM 缺陷: {errors}")

        proc = subprocess.run(
            [sys.executable, str(self.script_path), "--verify", str(tsv_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        self.assertNotEqual(proc.returncode, 0, "CLI 面对 BOM 必须返回非 0 退出码")

    def test_intercepts_crlf_line_endings(self) -> None:
        """变异拦截：带 CRLF (\\r\\n) 换行的文件必须被拦截。"""
        valid_content = "你好\tint. привет\n世界\tn. мир\n"
        tsv_path = self._write_temp_tsv(valid_content, crlf=True)

        _, errors = verify_table(tsv_path)
        self.assertTrue(any("carriage return" in e for e in errors), f"未拦截 CRLF 缺陷: {errors}")

        proc = subprocess.run(
            [sys.executable, str(self.script_path), "--verify", str(tsv_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        self.assertNotEqual(proc.returncode, 0, "CLI 面对 CRLF 必须返回非 0 退出码")

    def test_intercepts_invalid_part_of_speech(self) -> None:
        """变异拦截：非法词性标签必须被拦截。"""
        bad_pos_content = "世界\tinvalidpos. мир\n"
        tsv_path = self._write_temp_tsv(bad_pos_content)

        _, errors = verify_table(tsv_path)
        self.assertTrue(any("invalid part of speech" in e for e in errors), f"未拦截非法词性: {errors}")

        proc = subprocess.run(
            [sys.executable, str(self.script_path), "--verify", str(tsv_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        self.assertNotEqual(proc.returncode, 0, "CLI 面对非法词性必须返回非 0 退出码")

    def test_intercepts_english_leakage(self) -> None:
        """变异拦截：译词中混入英文字符必须被拦截。"""
        english_content = "电脑\tn. компьютер computer\n"
        tsv_path = self._write_temp_tsv(english_content)

        _, errors = verify_table(tsv_path)
        self.assertTrue(any("English character detected" in e for e in errors), f"未拦截英文泄漏: {errors}")

        proc = subprocess.run(
            [sys.executable, str(self.script_path), "--verify", str(tsv_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        self.assertNotEqual(proc.returncode, 0, "CLI 面对英文泄漏必须返回非 0 退出码")

    def test_intercepts_chinese_leakage(self) -> None:
        """变异拦截：译词中混入未翻译汉字必须被拦截。"""
        chinese_content = "电脑\tn. компьютер 计算机\n"
        tsv_path = self._write_temp_tsv(chinese_content)

        _, errors = verify_table(tsv_path)
        self.assertTrue(any("Chinese character detected" in e for e in errors), f"未拦截汉字残留: {errors}")

        proc = subprocess.run(
            [sys.executable, str(self.script_path), "--verify", str(tsv_path)],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        self.assertNotEqual(proc.returncode, 0, "CLI 面对汉字残留必须返回非 0 退出码")

    def test_intercepts_sorting_violation_and_duplicates(self) -> None:
        """变异拦截：顺序颠倒与重复词必须被拦截。"""
        # "世界" Unicode 为 0x4e16，"你好" 为 0x4f60。"世界" < "你好" 是正确的，但若反过来：
        reversal_content = "你好\tint. привет\n世界\tn. мир\n"
        tsv_path = self._write_temp_tsv(reversal_content)

        _, errors = verify_table(tsv_path)
        self.assertTrue(any("sorting violation" in e for e in errors), f"未拦截排序颠倒: {errors}")

        # 重复词
        duplicate_content = "世界\tn. мир\n世界\tn. вселенная\n"
        tsv_dup = self._write_temp_tsv(duplicate_content)
        _, errors_dup = verify_table(tsv_dup)
        self.assertTrue(any("duplicate word" in e for e in errors_dup), f"未拦截重复词: {errors_dup}")

    def test_intercepts_excessive_length_and_words(self) -> None:
        """变异拦截：超长译词（>40 字符）或超多词数（>4 词）必须被拦截。"""
        # 超长字符
        long_body = "а" * 45
        long_content = f"世界\tn. {long_body}\n"
        tsv_long = self._write_temp_tsv(long_content)
        _, errors_long = verify_table(tsv_long)
        self.assertTrue(any("exceeds length limit" in e for e in errors_long), f"未拦截超长字符: {errors_long}")

        # 超过 4 词
        words_content = "世界\tn. мир раз два три четыре пять\n"
        tsv_words = self._write_temp_tsv(words_content)
        _, errors_words = verify_table(tsv_words)
        self.assertTrue(any("exceeds limit of 4 words" in e for e in errors_words), f"未拦截超词数: {errors_words}")

    def test_intercepts_verb_non_infinitive(self) -> None:
        """变异拦截：动词标记为 v. 但非不定式原形必须被拦截。"""
        # "делает" 是第三人称单数变位，原形应是 "делать"
        non_inf_content = "做\tv. делает\n"
        tsv_path = self._write_temp_tsv(non_inf_content)

        _, errors = verify_table(tsv_path)
        self.assertTrue(any("is not in infinitive form" in e for e in errors), f"未拦截非不定式动词: {errors}")

    def test_intercepts_missing_senses_or_empty_body(self) -> None:
        """变异拦截：缺释义或空体必须被拦截。"""
        bad_line = "世界\t\n"
        tsv_path = self._write_temp_tsv(bad_line)
        _, errors = verify_table(tsv_path)
        self.assertTrue(any("missing senses" in e for e in errors), f"未拦截空释义: {errors}")


if __name__ == "__main__":
    unittest.main()
