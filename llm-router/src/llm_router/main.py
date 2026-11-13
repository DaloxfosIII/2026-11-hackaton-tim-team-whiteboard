
from Models import ModelChoices


def route_prompt_to_model(prompt: str) -> ModelChoices:
    """
    The wrapper function of our router. Will always return a model choice.
    """
    
    expected_metrics = predict_metrics(prompt)

    model_pick = pick_model(expected_metrics)

    return model_pick



def predict_metrics(prompt: str) -> MetricScores:
    """
    This function predicts the metrics that different models will receive on our
    prompt.
    """

    return MetricScores


def pick_model(MetricScores) -> ModelChoices:
    """
    This function uses the scored predicted metrics to pick the correct model.

    """

    return ModelChoices
