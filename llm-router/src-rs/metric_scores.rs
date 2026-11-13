//! Port of src/MetricScores.py.

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct MetricScores {
    /// Cost in USD
    pub cost: f64,
    /// Latency in seconds
    pub latency: f64,
    /// Quality on our defined scale; None = not scored yet
    pub quality: Option<f64>,
}
