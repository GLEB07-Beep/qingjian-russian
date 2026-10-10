//! 候选词数据模型。
//!
//! 翻译是候选词的 annotation：可选、单语言、最多 [`Translation::MAX_SENSES`] 条释义。
//! 不要把它扩展成多语言并列的结构，那会破坏「一次只学一种语言」的产品原则。

mod furigana;
mod kind;
mod language;
mod layout;
mod list;
mod part_of_speech;
mod sense;
mod translation;

use serde::{Deserialize, Serialize};

pub use furigana::{FuriganaSegment, furigana};
pub use kind::CandidateKind;
pub use language::{Language, UnknownLanguage};
pub use layout::{CandidateLayout, Cell, GRID_ROWS, Grid, MAX_CELL_EMS};
pub use list::CandidateList;
pub use part_of_speech::{PartOfSpeech, UnknownPartOfSpeech};
pub use sense::Sense;
pub use translation::Translation;

/// 一个可上屏的候选。
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Candidate {
    /// 上屏文本。
    pub text: String,

    /// 来源类型。
    pub kind: CandidateKind,

    /// 该候选对应的拼音音节，供平台层高亮已匹配部分。
    pub syllables: Vec<String>,

    /// 读音（如日语假名），中文候选暂不使用。
    pub reading: Option<String>,

    /// 学习语言下的译文；查不到或尚未就绪时为 `None`。
    pub translation: Option<Translation>,

    /// 候选带的辅码：筛码时是命中当前码段的那条，没在筛码（纯拼音态、辅码态空码段）时是词的
    /// 首条码（一词多码、多张码表取第一条）；没装码表或这个词没有码时为 `None`。
    /// 壳按 `[general] aux_code_show` 决定要不要显示。
    #[serde(default)]
    pub aux_code: Option<String>,
}

/// 将等级字符串格式化为候选框显示的友好标签。
pub fn format_level_badge(level: &str) -> &'static str {
    match level {
        "A1" => "A1 基础",
        "A2" => "A2 初级",
        "B1" => "B1 中级",
        "B2" => "B2 强化",
        "C1" => "C1 高级",
        "C2" => "C2 精通",
        "N5" => "N5 基础",
        "N4" => "N4 初级",
        "N3" => "N3 中级",
        "N2" => "N2 强化",
        "N1" => "N1 高级",
        _ => "考级",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn format_level_badge_matches_all_levels() {
        assert_eq!(format_level_badge("A1"), "A1 基础");
        assert_eq!(format_level_badge("A2"), "A2 初级");
        assert_eq!(format_level_badge("B1"), "B1 中级");
        assert_eq!(format_level_badge("B2"), "B2 强化");
        assert_eq!(format_level_badge("C1"), "C1 高级");
        assert_eq!(format_level_badge("C2"), "C2 精通");
        assert_eq!(format_level_badge("N5"), "N5 基础");
        assert_eq!(format_level_badge("N4"), "N4 初级");
        assert_eq!(format_level_badge("N3"), "N3 中级");
        assert_eq!(format_level_badge("N2"), "N2 强化");
        assert_eq!(format_level_badge("N1"), "N1 高级");
        assert_eq!(format_level_badge("unknown"), "考级");
    }
}


