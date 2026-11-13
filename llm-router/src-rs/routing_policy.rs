//! Port of src/RoutingPolicy.py.

use crate::model_choices::ModelChoice;

/// Prices that turn predicted metrics into one expected reward in USD.
///
/// reward = value_of_correct * quality - cost - latency_cost_per_s * latency
///
/// See "Economic Evaluation of LLMs" (arXiv 2507.03834) and "A Unified Approach
/// to Routing and Cascading for LLMs" (arXiv 2410.10347).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct RoutingPolicy {
    /// USD value of a fully correct answer (quality = 1)
    pub value_of_correct: f64,
    /// USD per second of waiting (0.008 for $30/hr)
    pub latency_cost_per_s: f64,
    /// Used when no model has a quality score
    pub fallback: ModelChoice,
}

pub const DEFAULT_POLICY: RoutingPolicy = RoutingPolicy {
    value_of_correct: 0.10,
    latency_cost_per_s: 0.0,
    fallback: ModelChoice::Sonnet,
};

impl Default for RoutingPolicy {
    fn default() -> Self {
        DEFAULT_POLICY
    }
}
