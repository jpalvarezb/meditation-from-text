import os
import re
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

model_path = "./emotion_model"  # relative to /app

# Prefer local ONNX model if present; otherwise fall back to a public HF model
if os.path.isdir(model_path):
    model = ORTModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
else:
    hf_model_id = "j-hartmann/emotion-english-distilroberta-base"
    model = AutoModelForSequenceClassification.from_pretrained(hf_model_id)
    tokenizer = AutoTokenizer.from_pretrained(hf_model_id)

classifier = pipeline(
    "text-classification", model=model, tokenizer=tokenizer, top_k=None
)


def preprocess_journal_entry(text: str) -> str:
    """
    Light-clean journal text for classification. Keeps emojis & expressive punctuation.
    """
    # Normalize quotes, keep expressiveness
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")

    # Strip non-printable control characters (but NOT emojis)
    text = "".join(c for c in text if c.isprintable())

    # Normalize spacing
    text = re.sub(r"\s+", " ", text).strip()

    return text


def emotion_classification(journal_entry: str) -> dict:
    """
    Classifies emotions from user's journal entry using HuggingFace pipeline.

    Parameters:
        journal_entry (str): User's journal reflection.

    Returns:
        Emotion classification with corresponding scores which add up to 1.
    """
    clean_text = preprocess_journal_entry(journal_entry)
    emotion_class = classifier(clean_text)[0]
    emotion_scores = {
        r["label"].lower(): r["score"]
        for r in sorted(emotion_class, key=lambda x: x["score"], reverse=True)
    }
    return emotion_scores
