from config.emotion_to_audio import EMOTION_TO_AUDIO


def choose_assets(emotion_scores: dict) -> dict:
    sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
    dominant_emotion, _ = sorted_emotions[0]
    return EMOTION_TO_AUDIO.get(dominant_emotion, EMOTION_TO_AUDIO["neutral"])
