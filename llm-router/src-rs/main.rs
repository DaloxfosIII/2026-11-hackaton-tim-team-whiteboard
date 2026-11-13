//! Rust port of src/main.py, for benchmarking against the Python router.
//!
//! Run with `cargo run --release` from the llm-router folder.

mod metric_scores;
mod model_choices;
mod routing_policy;

use std::collections::BTreeMap;
use std::sync::LazyLock;
use std::time::Instant;

use regex::Regex;

use metric_scores::MetricScores;
use model_choices::ModelChoice;
use routing_policy::{DEFAULT_POLICY, RoutingPolicy};

/// The wrapper function of our router. Will always return a model choice.
pub fn route_prompt_to_model(prompt: &str) -> ModelChoice {
    let expected_metrics = predict_metrics(prompt);

    pick_model(&expected_metrics, &DEFAULT_POLICY)
}

/// Word stems that ask for reasoning, mechanisms or discussion rather than a single fact.
/// Compiled once on first use, like the module-level `re.compile` in Python.
/// `\b` and `\w` are Unicode-aware here, as in Python's `re`.
static EXPLANATORY: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(concat!(
        r"(?i)\b(",
        r"why|explain\w*|describe\w*|discuss\w*|compare\w*|contrast\w*|analy[sz]\w*|evaluate\w*|",
        r"elaborate\w*|justify|argue\w*|argument\w*|counterargument\w*|present|",
        r"differences?|pros and cons|advantages|disadvantages|implications?|",
        r"how (?:does|do|did|can|could|would|is|are)",
        r")\b",
    ))
    .expect("EXPLANATORY regex is valid")
});

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum QuestionClass {
    Explanatory,
    Factual,
}

/// Per-class medians of the measured results in tests/test_cases (10 cases, 2026-11-13),
/// as fitted by tests/predict_metrics/candidate_functions/question_type_median.py.
/// Keep in sync with `_CLASS_MEDIANS` in src/main.py.
fn class_medians(label: QuestionClass) -> BTreeMap<ModelChoice, MetricScores> {
    let s = |cost, latency, quality| MetricScores { cost, latency, quality: Some(quality) };
    match label {
        QuestionClass::Explanatory => BTreeMap::from([
            (ModelChoice::Haiku, s(0.0005853, 6.307, 4.5)),
            (ModelChoice::Sonnet, s(0.006388, 5.331, 4.5)),
            (ModelChoice::Opus, s(0.018312, 8.721, 5.0)),
        ]),
        QuestionClass::Factual => BTreeMap::from([
            (ModelChoice::Haiku, s(0.0000323, 1.202, 5.0)),
            (ModelChoice::Sonnet, s(0.000896, 1.316, 4.0)),
            (ModelChoice::Opus, s(0.001572, 1.562, 5.0)),
        ]),
    }
}

pub fn is_explanatory(prompt: &str) -> bool {
    EXPLANATORY.is_match(prompt)
}

/// Predicts the metrics that different models will receive on our prompt.
///
/// Classifies the prompt as explanatory ("why ...", "explain ...", "compare ...")
/// or matter-of-fact, and returns each model's median measured cost, latency and
/// quality for that class. Quality is on the 0-5 scale from tests/quality_scale.md.
pub fn predict_metrics(prompt: &str) -> BTreeMap<ModelChoice, MetricScores> {
    let label = if is_explanatory(prompt) {
        QuestionClass::Explanatory
    } else {
        QuestionClass::Factual
    };
    class_medians(label)
}

/// Expected net value of a call in USD. Requires a quality score.
pub fn expected_reward(scores: &MetricScores, policy: &RoutingPolicy) -> f64 {
    let quality = scores.quality.expect("expected_reward requires a quality score");
    policy.value_of_correct * quality - scores.cost - policy.latency_cost_per_s * scores.latency
}

/// Uses the scored predicted metrics to pick the correct model.
///
/// Picks the model with the highest expected reward (see RoutingPolicy); ties go
/// to the cheaper model. Models without a quality score are skipped, and if none
/// has one, the policy's fallback is returned.
///
/// Panics on an empty map, where the Python version raises ValueError.
pub fn pick_model(scores: &BTreeMap<ModelChoice, MetricScores>, policy: &RoutingPolicy) -> ModelChoice {
    assert!(!scores.is_empty(), "pick_model needs at least one candidate model");

    // Higher reward wins; on equal reward, the lower cost wins (cost is negated).
    // Only a strictly greater key replaces the best, so full ties keep the first
    // model in iteration order, exactly like Python's max().
    let mut best: Option<(ModelChoice, (f64, f64))> = None;
    for (&model, model_score) in scores.iter().filter(|(_, s)| s.quality.is_some()) {
        let key = (expected_reward(model_score, policy), -model_score.cost);
        if best.is_none_or(|(_, best_key)| key > best_key) {
            best = Some((model, key));
        }
    }

    match best {
        Some((model, _)) => model,
        None => {
            eprintln!("WARNING:main:No model has a quality score; using fallback {}", policy.fallback);
            policy.fallback
        }
    }
}

/// Number of timed route_prompt_to_model calls (keep equal to BENCH_RUNS in src/main.py).
const BENCH_RUNS: usize = 20;

fn print_bench(times_us: &[f64]) {
    let min = times_us.iter().copied().fold(f64::INFINITY, f64::min);
    let max = times_us.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    let mean = times_us.iter().sum::<f64>() / times_us.len() as f64;
    println!(
        "route_prompt_to_model x{}: mean {mean:.3} us, min {min:.3} us, max {max:.3} us",
        times_us.len()
    );
}

fn main() {
    let start = Instant::now();

    let prompt = "Write a haiku about routers.";
    eprintln!("INFO:main:Prompt: {prompt:?}");
    eprintln!("INFO:main:Picked model: {}", route_prompt_to_model(prompt));

    // Time the routing itself, call by call. black_box stops the optimiser
    // from skipping calls whose result is unused.
    let mut times_us = Vec::with_capacity(BENCH_RUNS);
    for _ in 0..BENCH_RUNS {
        let t = Instant::now();
        std::hint::black_box(route_prompt_to_model(std::hint::black_box(prompt)));
        times_us.push(t.elapsed().as_secs_f64() * 1e6);
    }
    print_bench(&times_us);

    let elapsed = start.elapsed();
    println!("Total runtime: {:.3} ms", elapsed.as_secs_f64() * 1000.0);
}
