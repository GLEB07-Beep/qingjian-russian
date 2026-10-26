//! 候选排序。
//!
//! 词级排序规则：
//! 1. 音节数与输入完全一致的词优先（`kaifa` → 开发 排在 开发者 前）
//! 2. 覆盖输入字母多者优先（`kaif` → 开发者 排在 开 前）
//! 3. 切分里非末尾的简拼音节少者优先（`kaifa` 按 `kai fa` 读的 开放 排在按 `kai f a` 读的 开放啊 前）
//! 4. 最后一个音节完整匹配优先（`kaifa` → 开发 排在 开放 前）
//! 5. 注音敲了声调时，声调代价小者优先（ㄇㄚ 一声 → 妈 排在 吗 前；表与规则见 `zhuyin::tone`）
//! 6. 同一输入串下用户选过的次数（Learner 的 `choice_weight`：`mgs` 选过 美国式，下次 `mgs` 它就是首选）
//! 7. 上下文得分：语言模型给的 `log P(词 | 上一个上屏的词)`（个人 bigram 插值，模型不认识的按词库词频兜底并扣分，
//!    见 `sentence::transition_log_prob`）加用户选择次数的加分（[`weight_bonus`]，对数且封顶），模糊音命中扣 ln 2、
//!    敲错变体命中扣那类敲错的代价（`correction::TypoKind::cost`，个人敲错表打折）。
//!    这样 `ba` 在「做了」后面出 吧、句首出 把；纯词频排序两处都只能出同一个
//! 8. 敲的原音节优先，词长短者优先，最后按字符串稳定排序保证结果可复现
//!
//! 词库静态词频只用于预选（命中太多时先按词频砍到够排的量）与兜底。
//!
//! 排完再由 [`arrange`] 按类别重排一次：首音节的单字不被猜出来的长词、拆开音节的读法与几十个同音整词挤到几页之后。

mod scored;

use std::collections::HashSet;

pub use scored::{PreselectKey, Scored, SortKey};

/// 用户选择次数的加分系数：加分 = 系数 × ln(1 + min(次数, [`WEIGHT_CAP`]))。
/// 这个加分只负责「同音词里偏向用户常选的那个」，所以既取对数又封顶（最多约 1.5 分，e^1.5 ≈ 4.5 倍），
/// 让上下文（bigram）仍能压过它；不封顶时选过 173 次的 的 会带着 5 分加分把任何含 的 的拆分路径抬到整词之上
/// （`haode` 出 号的 而不是 好的）。用户用得多的词另有个人 bigram 里的一元项撑腰，不靠这里。
pub const WEIGHT_BONUS: f64 = 0.5;

/// 加分里计入的选择次数上限。
pub const WEIGHT_CAP: u32 = 20;

/// 模糊音命中扣的分（词频减半）。敲错变体的代价见 `correction::TypoKind`。
pub const FUZZY_PENALTY: f64 = std::f64::consts::LN_2;

/// 预测补全（以输入为前缀、多出几个没敲的音节的长词：`shishan` → 时尚潮流）排在前缀词之前的最多条数，其余排到前缀词后面。
/// 整段没有词时第二页起就该是逐字选的单字（`shishan` 要 屎山，词库里没有），而不是几十个猜出来的长词。
pub const COMPLETIONS_BEFORE_PREFIXES: usize = 3;

/// 首音节最好的几个单字提前：排在前缀词的第几个之后（长输入整段没有词时，前面是 实验室、十堰市 这类盖住开头几个音节的词）。
pub const PREFIXES_BEFORE_SINGLE_CHARS: usize = 2;

/// 提前几个首音节单字（#769：首页保底单字）。
pub const EARLY_SINGLE_CHARS: usize = 2;

/// 有整词时拆开音节的读法排在首音节的几个单字之后（一页）。
pub const SINGLE_CHARS_BEFORE_SPLIT: usize = 9;

/// 首音节单字之前最多几个整词：再加三条猜测，单字最晚在第二页出现。
pub const WORDS_BEFORE_SINGLE_CHARS: usize = 12;

/// 用户选择次数换算成得分加成，词级排序与整句路径共用，见 [`WEIGHT_BONUS`]。
pub fn weight_bonus(count: u32) -> f64 {
    WEIGHT_BONUS * (1.0 + f64::from(count.min(WEIGHT_CAP))).ln()
}

/// 排序并按词文本去重（同一个词可能被多种切分命中，保留得分最高的一条），最多留 `limit` 条。
/// `context` 给每条命中算（同输入串下的选择次数, 上下文 log 概率），只对预选后剩下的那些调用。
///
/// 排序键先算好再排：单字母简拼能命中两万条，比较器里每次数字符数会让排序占掉几十毫秒；去重也只做到够数为止。
pub fn rank(
    items: &mut Vec<Scored<'_>>,
    limit: usize,
    context: impl Fn(&Scored<'_>) -> (u32, f64),
) {
    // 远超上限时先按结构键 + 词频线性选出前面一段：同一个词会被多种切分命中，多选一倍留给去重（结果仍可能略少于上限，无妨）
    let preselect = limit.saturating_mul(2);
    if items.len() > preselect.saturating_mul(2) {
        let mut keyed: Vec<(PreselectKey, Scored<'_>)> = items
            .drain(..)
            .map(|item| (item.preselect_key(), item))
            .collect();
        keyed.select_nth_unstable_by(preselect, |a, b| b.0.cmp(&a.0));
        keyed.truncate(preselect);
        items.extend(keyed.into_iter().map(|(_, item)| item));
    }
    let mut keyed: Vec<(SortKey<'_>, Scored<'_>)> = items
        .drain(..)
        .map(|item| {
            let (choice, log_prob) = context(&item);
            let score = log_prob + weight_bonus(item.weight) - item.penalty;
            (item.key(choice, score), item)
        })
        .collect();
    keyed.sort_unstable_by(|a, b| a.0.cmp(&b.0));
    let mut seen: HashSet<&str> = HashSet::with_capacity(limit.min(keyed.len()));
    items.extend(
        keyed
            .into_iter()
            .map(|(_, item)| item)
            .filter(|item| seen.insert(item.hit.text))
            .take(limit),
    );
}

/// 排好序之后按类别重排一次，各类内部保持 [`rank`] 的顺序：
/// 1. 盖住整段、读音就是敲的那几个音节的词，至多 [`WORDS_BEFORE_SINGLE_CHARS`] 个，再多的排到第 3 类的头一页单字之后；
/// 2. 至多 [`COMPLETIONS_BEFORE_PREFIXES`] 条猜测：比敲的多出音节的长词（`shishan` → 时尚潮流）、把打完的末音节读成更长音节的词
///    （`shan` 读成 `shang` 的 事上）。只在 `clean`（输入有一种全是完整音节的切法）时算猜测：末音节还没打完时（`jixub`）
///    补全正是用户要往下打的，照 [`rank`] 的顺序留在第 1 类；
/// 3. 只盖住开头一段的词与单字（长的在前）。没有一个词盖住整段时（#769），首音节最好的 [`EARLY_SINGLE_CHARS`] 个单字
///    提到前 [`PREFIXES_BEFORE_SINGLE_CHARS`] 个之后，第一页就有字可以逐字选；
/// 4. 其余猜测；
/// 5. 拆开音节的读法——只在有词的读音正好是敲的音节（第 1、2 类不空）时往后放，放在第 3 类首音节的头 [`SINGLE_CHARS_BEFORE_SPLIT`] 个单字之后；一个都没有时（`wodei` 的 我的、
///    `cankai` 的 参考、`mingtia` 的 明天）它们多半是手误或没打完，正是用户要的，照前四类的规则排。
///
/// `whole` 是整段输入的字母数，`first` 是最好那种切法首音节的字母数（`daoshih` 是 `dao` 的 3，不是简拼 `d` 的 1）。
/// `chosen` 为真的（这个输入串下选过）留在第 1 类，不挪。输入只有一个音节时没有前缀词，顺序与 [`rank`] 一样。
pub fn arrange(
    items: &mut Vec<Scored<'_>>,
    whole: usize,
    first: usize,
    clean: bool,
    chosen: impl Fn(&Scored<'_>) -> bool,
) {
    let worded = items
        .iter()
        .any(|item| !item.split && item.coverage >= whole);
    let mut head = Vec::with_capacity(items.len());
    let mut guesses = Vec::new();
    let mut prefixes = Vec::new();
    let mut split = Vec::new();
    for item in items.drain(..) {
        if chosen(&item) {
            head.push(item);
        } else if item.split && worded {
            split.push(item);
        } else if item.coverage < whole {
            prefixes.push(item);
        } else if clean && (!item.hit.exact || !item.full_last) {
            guesses.push(item);
        } else {
            head.push(item);
        }
    }
    if head.is_empty() && guesses.is_empty() {
        let mut singles = Vec::new();
        let mut index = PREFIXES_BEFORE_SINGLE_CHARS;
        while index < prefixes.len() && singles.len() < EARLY_SINGLE_CHARS {
            let item = &prefixes[index];
            if item.coverage == first && item.hit.text.chars().count() == 1 {
                singles.push(prefixes.remove(index));
            } else {
                index += 1;
            }
        }
        let at = PREFIXES_BEFORE_SINGLE_CHARS.min(prefixes.len());
        prefixes.splice(at..at, singles);
    }
    let late = guesses.split_off(guesses.len().min(COMPLETIONS_BEFORE_PREFIXES));
    // 拆开的读法跟在首音节的头一页单字后面，不沉到几百个单字之后：有整词时它们也常是手误的兜底（`guanle` 的 管理）
    let mut singles = 0;
    let cut = prefixes
        .iter()
        .position(|item| {
            singles += usize::from(item.coverage == first && item.hit.text.chars().count() == 1);
            singles > SINGLE_CHARS_BEFORE_SPLIT
        })
        .unwrap_or(prefixes.len());
    let rest = prefixes.split_off(cut);
    // 整词太多（`zhiyi` 读得出五十多个）时，后面的也排到这一页单字之后，否则单字要翻好几页（#769）
    let more = if prefixes.is_empty() {
        Vec::new()
    } else {
        head.split_off(head.len().min(WORDS_BEFORE_SINGLE_CHARS))
    };
    items.extend(head);
    items.extend(guesses);
    items.extend(prefixes);
    items.extend(more);
    items.extend(split);
    items.extend(rest);
    items.extend(late);
}

#[cfg(test)]
mod tests {
    use super::*;
    use qingjian_dictionary::Match;

    fn hit<'a>(text: &'a str, pinyin: &'a str, frequency: u32, exact: bool) -> Match<'a> {
        Match {
            text,
            pinyin,
            frequency,
            reading_total: 0,
            tones: Default::default(),
            secondary: false,
            exact,
        }
    }

    #[test]
    fn exact_beats_frequency_and_weight_beats_static_frequency() {
        let mut items = vec![
            Scored {
                hit: hit("开发者", "kai fa zhe", 99999, false),
                full_last: true,
                coverage: 5,
                abbreviated: 0,
                weight: 0,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
            Scored {
                hit: hit("开放", "kai fang", 20000, true),
                full_last: false,
                coverage: 5,
                abbreviated: 0,
                weight: 5,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
            Scored {
                hit: hit("开发", "kai fa", 9000, true),
                full_last: true,
                coverage: 5,
                abbreviated: 0,
                weight: 0,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
        ];
        rank(&mut items, usize::MAX, |_| (0, 0.0));
        let texts: Vec<&str> = items.iter().map(|s| s.hit.text).collect();
        assert_eq!(texts, ["开发", "开放", "开发者"]);
    }

    #[test]
    fn context_score_orders_within_the_same_structure() {
        let mut items = vec![
            Scored {
                hit: hit("把", "ba", 3_000_000, true),
                full_last: true,
                coverage: 2,
                abbreviated: 0,
                weight: 0,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
            Scored {
                hit: hit("吧", "ba", 2_000_000, true),
                full_last: true,
                coverage: 2,
                abbreviated: 0,
                weight: 0,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
        ];
        // 上下文说 吧 更像：词频高的 把 让位
        let by_context = |s: &Scored<'_>| (0, if s.hit.text == "吧" { -1.0 } else { -6.0 });
        rank(&mut items, usize::MAX, by_context);
        let texts: Vec<&str> = items.iter().map(|s| s.hit.text).collect();
        assert_eq!(texts, ["吧", "把"]);
        // 同一输入串下选过的压过上下文
        rank(&mut items, usize::MAX, |s| {
            (
                u32::from(s.hit.text == "把"),
                if s.hit.text == "吧" { -1.0 } else { -6.0 },
            )
        });
        assert_eq!(items[0].hit.text, "把");
        // 同分时用户选过的、非模糊音的靠前
        for item in &mut items {
            item.weight = u32::from(item.hit.text == "把") * 3;
        }
        rank(&mut items, usize::MAX, |_| (0, -2.0));
        assert_eq!(items[0].hit.text, "把");
        for item in &mut items {
            item.weight = 3;
            item.penalty = if item.hit.text == "把" {
                FUZZY_PENALTY
            } else {
                0.0
            };
        }
        rank(&mut items, usize::MAX, |_| (0, -2.0));
        assert_eq!(items[0].hit.text, "吧");
    }

    #[test]
    fn fewer_abbreviated_syllables_win_at_equal_coverage() {
        let mut items = vec![
            Scored {
                hit: hit("开放啊", "kai fang a", 132, true),
                full_last: true,
                coverage: 5,
                abbreviated: 1,
                weight: 0,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
            Scored {
                hit: hit("开放", "kai fang", 500_000, true),
                full_last: false,
                coverage: 5,
                abbreviated: 0,
                weight: 0,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
        ];
        rank(&mut items, usize::MAX, |_| (0, 0.0));
        assert_eq!(items[0].hit.text, "开放");
    }

    #[test]
    fn weight_bonus_is_logarithmic_and_capped() {
        assert_eq!(weight_bonus(0), 0.0);
        assert!(weight_bonus(1) < weight_bonus(10));
        assert_eq!(weight_bonus(WEIGHT_CAP), weight_bonus(WEIGHT_CAP * 50));
        assert!(weight_bonus(u32::MAX) < 1.6);
    }

    #[test]
    fn deduplicates_by_text_keeping_best() {
        let mut items = vec![
            Scored {
                hit: hit("西安", "xi an", 4000, false),
                full_last: true,
                coverage: 4,
                abbreviated: 0,
                weight: 0,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
            Scored {
                hit: hit("西安", "xi an", 4000, true),
                full_last: true,
                coverage: 4,
                abbreviated: 0,
                weight: 0,
                penalty: 0.0,
                tone_cost: 0,
                split: false,
            },
        ];
        rank(&mut items, usize::MAX, |_| (0, 0.0));
        assert_eq!(items.len(), 1);
        assert!(items[0].hit.exact);
    }
}
