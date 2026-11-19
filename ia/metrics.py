import re

VOWEL_CLUSTER_RE = re.compile(r"[aeiouáéíóúâêîôûãõàü]+", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
SENTENCE_SPLIT_RE = re.compile(r"[.!?;\n]+")


def _count_portuguese_syllables(word: str) -> int:
    """Estimate syllable count in Portuguese based on vowel clusters."""
    clusters = VOWEL_CLUSTER_RE.findall(word)
    return max(1, len(clusters))


def count_words(text: str) -> int:
    """Count alphanumeric words in text."""
    return len(WORD_RE.findall(text or ""))


def calculate_portuguese_readability(text: str) -> float:
    """Compute Flesch Reading Ease adapted for Brazilian Portuguese (Martins et al.).

    Formula: 248.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    Clamped to [0.0, 100.0], where higher scores mean easier reading.
    """
    words = WORD_RE.findall(text or "")
    if not words:
        return 0.0

    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(text or "") if s.strip()]
    sentence_count = max(1, len(sentences))
    word_count = len(words)
    syllable_count = sum(_count_portuguese_syllables(w) for w in words)

    score = (
        248.835
        - 1.015 * (word_count / sentence_count)
        - 84.6 * (syllable_count / word_count)
    )
    return round(max(0.0, min(100.0, score)), 1)


def classify_readability(score: float) -> str:
    """Map Flesch pt-BR score into an intuitive Portuguese reading difficulty label."""
    if score >= 75.0:
        return "Muito Fácil"
    if score >= 50.0:
        return "Fácil"
    if score >= 25.0:
        return "Médio"
    return "Muito Difícil (Juridiquês)"


def estimate_reading_time_sec(word_count: int, words_per_minute: int = 150) -> int:
    """Estimate reading comprehension time in seconds."""
    if word_count <= 0:
        return 0
    return max(1, round((word_count / words_per_minute) * 60))


def compute_translation_metrics(original_text: str, bullets: list[str]) -> dict[str, object]:
    """Calculate before-vs-after readability, word compression, and time saved."""
    summary_text = " ".join(
        b.rstrip(" .") + "." for b in bullets if isinstance(b, str) and b.strip()
    )

    original_words = count_words(original_text)
    summary_words = count_words(summary_text)

    flesch_before = calculate_portuguese_readability(original_text)
    flesch_after = calculate_portuguese_readability(summary_text)

    # Dense legal prose is read slower (~120 WPM) than plain-language bullets (~180 WPM).
    time_before_sec = estimate_reading_time_sec(original_words, words_per_minute=120)
    time_after_sec = estimate_reading_time_sec(summary_words, words_per_minute=180)
    time_saved_sec = max(0, time_before_sec - time_after_sec)

    reduction_pct = (
        round(((original_words - summary_words) / original_words) * 100, 1)
        if original_words > 0
        else 0.0
    )

    return {
        "original_word_count": original_words,
        "summary_word_count": summary_words,
        "word_reduction_pct": max(0.0, reduction_pct),
        "flesch_before": flesch_before,
        "flesch_after": flesch_after,
        "readability_gain_points": round(flesch_after - flesch_before, 1),
        "level_before": classify_readability(flesch_before),
        "level_after": classify_readability(flesch_after),
        "reading_time_before_sec": time_before_sec,
        "reading_time_after_sec": time_after_sec,
        "reading_time_saved_sec": time_saved_sec,
    }
