//! 候选窗口的一行：[`Candidate`] → 渲染器的 [`Row`]（序号、候选词、annotation 片段），与 macOS 端 `candidates/row.rs` 一致。
//! GDI 画法也用同一个类型。

use qingjian_core::{Candidate, CandidateKind};
use qingjian_render::{Row, Tone};

/// `position` 是页内下标（从 0 起）。`show_code` 是 `[general] aux_code_show`：
/// 打开且候选带码时，码用方括号括起来紧跟在候选词后面（`鹤[rbm]`），不进 annotation。
pub(crate) fn from_candidate(position: usize, candidate: &Candidate, show_code: bool) -> Row {
    let code = candidate
        .aux_code
        .as_ref()
        .filter(|_| show_code)
        .map(|code| format!("[{code}]"));
    let mut annotation = Vec::new();
    if let Some(reading) = &candidate.reading {
        annotation.push((reading.clone(), Tone::Gloss));
    }
    if let Some(translation) = &candidate.translation {
        for (i, sense) in translation.senses().iter().enumerate() {
            if i > 0 || !annotation.is_empty() {
                annotation.push((" · ".to_owned(), Tone::Faint));
            }
            if let Some(pos) = sense.part_of_speech {
                annotation.push((format!("{pos} "), Tone::Faint));
            }
            let tone = if sense.fresh {
                Tone::Fresh
            } else {
                Tone::Gloss
            };
            for segment in sense.furigana() {
                annotation.push((segment.text, tone));
                if let Some(reading) = segment.reading {
                    annotation.push((format!("({reading})"), Tone::Faint));
                }
            }
            if let Some(level) = &sense.level {
                annotation.push((
                    format!("  [{}]", qingjian_core::format_level_badge(level)),
                    Tone::Fresh,
                ));
            }
        }
    }
    Row {
        index: (position + 1).to_string(),
        text: candidate.text.clone(),
        code,
        annotation,
        cloud: candidate.kind == CandidateKind::Cloud,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use qingjian_core::{PartOfSpeech, Sense, Translation};

    #[test]
    fn row_renders_level_badge_when_present() {
        let candidate = Candidate {
            text: "你".into(),
            kind: CandidateKind::Chinese,
            syllables: vec!["ni".into()],
            reading: None,
            translation: Some(Translation::new(
                qingjian_core::Language::Russian,
                vec![Sense {
                    part_of_speech: Some(PartOfSpeech::Pronoun),
                    text: "ты".into(),
                    reading: None,
                    fresh: true,
                    level: Some("A1".into()),
                }],
            )),
            aux_code: None,
        };
        let row = from_candidate(0, &candidate, false);
        assert_eq!(row.index, "1");
        assert_eq!(row.text, "你");
        assert_eq!(
            row.annotation,
            vec![
                ("pron. ".to_string(), Tone::Faint),
                ("ты".to_string(), Tone::Fresh),
                ("  [A1 基础]".to_string(), Tone::Fresh),
            ]
        );
    }

    #[test]
    fn row_does_not_render_level_badge_when_absent() {
        let candidate = Candidate {
            text: "你好".into(),
            kind: CandidateKind::Chinese,
            syllables: vec!["ni".into(), "hao".into()],
            reading: None,
            translation: Some(Translation::new(
                qingjian_core::Language::Russian,
                vec![Sense {
                    part_of_speech: None,
                    text: "привет".into(),
                    reading: None,
                    fresh: false,
                    level: None,
                }],
            )),
            aux_code: None,
        };
        let row = from_candidate(0, &candidate, false);
        assert_eq!(row.annotation, vec![("привет".to_string(), Tone::Gloss)]);
    }
}

