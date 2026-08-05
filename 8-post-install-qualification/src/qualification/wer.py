import werpy


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Computes Word Error Rate using werpy, the WER library used elsewhere in
    the Vulavula stack (vulavula-common, evalkit, their-cloud-mvp), so accuracy
    numbers from this qualification script are directly comparable to theirs.
    """
    if not reference.strip() and not hypothesis.strip():
        return 0.0

    normalized_reference = werpy.normalize(reference)
    normalized_hypothesis = werpy.normalize(hypothesis)

    if not normalized_reference:
        return 0.0 if not normalized_hypothesis else 1.0

    return float(werpy.wer(normalized_reference, normalized_hypothesis))
