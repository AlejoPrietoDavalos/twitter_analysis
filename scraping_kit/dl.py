
def instance_classifier():
    from transformers import pipeline
    from transformers.pipelines.zero_shot_classification import ZeroShotClassificationPipeline
    return pipeline(
        "zero-shot-classification",
        model = "facebook/bart-large-mnli"
    )

