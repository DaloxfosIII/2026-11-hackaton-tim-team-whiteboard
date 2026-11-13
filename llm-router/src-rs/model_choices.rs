//! Port of src/ModelChoices.py.
//!
//! An enum is the Rust counterpart of the Python `Literal`: the compiler rejects
//! any other model. The derived ordering follows the declaration order, so a
//! `BTreeMap<ModelChoice, _>` iterates in the same order as the Python dicts.

use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ModelChoice {
    Haiku,
    Sonnet,
    Opus,
}

impl ModelChoice {
    /// Every model, in declaration order (Python: `ModelChoices`).
    #[allow(dead_code)]
    pub const ALL: [ModelChoice; 3] = [ModelChoice::Haiku, ModelChoice::Sonnet, ModelChoice::Opus];

    /// The exact Claude API model ID.
    pub const fn as_str(self) -> &'static str {
        match self {
            ModelChoice::Haiku => "claude-haiku-5-5",
            ModelChoice::Sonnet => "claude-sonnet-5-5",
            ModelChoice::Opus => "claude-opus-5-5",
        }
    }

    /// Short tier name used in test result file names (Python: `TIERS`).
    #[allow(dead_code)]
    pub fn from_tier(tier: &str) -> Option<ModelChoice> {
        match tier {
            "haiku" => Some(ModelChoice::Haiku),
            "sonnet" => Some(ModelChoice::Sonnet),
            "opus" => Some(ModelChoice::Opus),
            _ => None,
        }
    }
}

impl fmt::Display for ModelChoice {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}
