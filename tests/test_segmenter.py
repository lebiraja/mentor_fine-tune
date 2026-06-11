"""Sentence segmenter: streaming cuts, abbreviations, flush, max-chunk valve."""

from backend.core.segmenter import MAX_CHUNK_CHARS, SentenceSegmenter


def test_emits_sentence_on_boundary():
    seg = SentenceSegmenter()
    out = seg.feed("Life is not a problem to be solved. It is a reality")
    assert out == ["Life is not a problem to be solved."]
    assert seg.flush() == ["It is a reality"]


def test_accumulates_across_deltas():
    seg = SentenceSegmenter()
    assert seg.feed("Courage is ") == []
    assert seg.feed("not the absence of fear") == []
    assert seg.feed(". And then") == ["Courage is not the absence of fear."]


def test_short_fragments_not_emitted_alone():
    seg = SentenceSegmenter()
    # "Yes." is under the min length, held until more text arrives
    assert seg.feed("Yes. ") == []
    out = seg.feed("That feeling is worth examining closely. ")
    assert out == ["Yes. That feeling is worth examining closely."]


def test_abbreviations_do_not_split():
    seg = SentenceSegmenter()
    out = seg.feed("Think about what Dr. Frankl wrote in his book. More text")
    assert out == ["Think about what Dr. Frankl wrote in his book."]


def test_question_and_exclamation_boundaries():
    seg = SentenceSegmenter()
    out = seg.feed("What do you actually control here? Quite a lot! And more")
    assert out == ["What do you actually control here?", "Quite a lot!"]


def test_max_chunk_safety_valve():
    seg = SentenceSegmenter()
    long_text = ("word " * 80) + "tail, " + ("word " * 20)
    out = seg.feed(long_text)
    assert out, "oversized chunk should be force-cut"
    assert all(len(s) <= MAX_CHUNK_CHARS + 1 for s in out)


def test_flush_empty():
    assert SentenceSegmenter().flush() == []
