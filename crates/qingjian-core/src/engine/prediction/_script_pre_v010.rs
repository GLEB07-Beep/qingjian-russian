//! 翻译选中文字的方向：看选区里的文字主要是哪种文字，决定译成学习语言还是译回中文。

use crate::candidate::Language;

/// 选中的文字该译成什么语言：主要是汉字 → 学习语言（学习语言是中文时退到英文）；
/// 有假名，或者拉丁字母不少于汉字 → 中文。只按字符统计，不猜语种细节，剩下的交给模型（提示词里写了「已是目标语言就译成中文」）。
pub fn translation_target(text: &str, learning: Language) -> Language {
    let mut han = 0usize;
    let mut kana = 0usize;
    let mut latin = 0usize;
    for c in text.chars() {
        if is_kana(c) {
            kana += 1;
        } else if is_han(c) {
            han += 1;
        } else if c.is_ascii_alphabetic() || is_latin_extended(c) {
            latin += 1;
        }
    }
    let to_chinese = kana > 0 || latin >= han;
    if to_chinese {
        return Language::Chinese;
    }
    match learning {
        Language::Chinese => Language::English,
        other => other,
    }
}

fn is_han(c: char) -> bool {
    matches!(c as u32,
        0x3400..=0x4DBF | 0x4E00..=0x9FFF | 0xF900..=0xFAFF | 0x20000..=0x323AF | 0x3005 | 0x3007)
}

fn is_kana(c: char) -> bool {
    matches!(c as u32, 0x3041..=0x309F | 0x30A0..=0x30FF | 0x31F0..=0x31FF | 0xFF66..=0xFF9F)
}

/// 带变音符的拉丁字母（café、naïve）也算字母。
fn is_latin_extended(c: char) -> bool {
    matches!(c as u32, 0x00C0..=0x024F) && c.is_alphabetic()
}
