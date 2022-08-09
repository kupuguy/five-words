import pytest

from words.words import has_last_word


@pytest.mark.parametrize(
    "used,words,expected",
    [
        (0b1_11111_11111_11111_11110_00000, {0b1_11110: 1}, True),
        (0b1_11111_11111_11111_11110_00000, {0b0_11111: 1}, True),
        (0b1_11111_11111_11111_11110_00000, {0b1_10111: 1}, True),
        (0b1_11111_11111_11111_11110_00000, {0b11_01110: 1}, False),
    ],
)
def test_has_last_word(used: int, words: dict[int], expected: bool) -> None:
    actual = has_last_word(words, used)
    assert expected == actual
