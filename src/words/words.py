"""
Program to find combinations of five 5-letter words that use exactly 25 different letters of the alphabet.

1. Load words, discard any with repeated letters, convert each word to a bitset.

bitsets are used to represent collections of letters. A=1, B=2, ...

This means each group of unique letters can be held in a single 32 bit integer but it also allows a bunch of
useful functions be computed easily:
    union: a | b
    intersection: a & b
    alphabetically first letter in the set: ((~a + 1) & a)
    alphabetically first letter not in the set: ((a|mask + 1) & ~(a|mask))
    where mask is ((~a + 1) & a) - 1
"""
from __future__ import annotations

import string
from pathlib import Path
from typing import Sequence

from rich.progress import Progress

LETTERS: dict[str, int] = {
    letter: (1 << index) for index, letter in enumerate(string.ascii_lowercase)
}
MASKS: dict[int, int] = {value: value - 1 for letter, value in LETTERS.items()}
ALL_LETTERS = (1 << 26) - 1

LETTER_A = LETTERS["a"]
LETTER_B = LETTERS["b"]
LETTER_C = LETTERS["c"]


def load_words(input_words: Path, progress: Progress) -> dict[int, set[str]]:
    word_list: dict[int, set[str]] = {}
    with progress.open(input_words, "r", description="Loading...") as file:
        for word in file:
            word = word.strip().lower()
            if len(word) == 5 and len(set(word)) == 5:
                bitset = sum(LETTERS[c] for c in word)
                if bitset in word_list:
                    word_list[bitset].add(word)
                else:
                    word_list[bitset] = {word}

    return word_list


def index_bitsets(
    word_list: dict[int, object], progress: Progress
) -> dict[int, list[int]]:
    """Returns a dict mapping each letter to a list of the bitsets with this as the earliest letter they contain"""
    index = {letter: [] for letter in LETTERS.values()}
    for word in progress.track(word_list, description="Indexing..."):
        index[(~word + 1) & word].append(word)

    return {k: index[k] for k in index if index[k]}


def solution_masks(word_list: dict[int, object]) -> set[int]:
    """Build a set of all possible 20 bit values that have a valid solution"""
    solutions: set[int] = set()
    for word in word_list:
        for letter in MASKS:
            if not (word & letter):
                solutions.add((word | letter) ^ ALL_LETTERS)
    return solutions


def make_pairs(
    word_index: dict[int, list[int]], progress: Progress
) -> dict[int, set[int]]:
    """
    Combine each word with every other word where there is no letter in common.
    Returns a dictionary mapping the pair bitset to a set of word bitsets used to construct it.
    Only one word from each pair is stored, the other can be calculated.
    """
    pair_bitset: dict[int, set[int]] = {}
    last_start = max(word_index)
    for first_letter, mask in progress.track(MASKS.items(), description="Pairing..."):
        if first_letter not in word_index:
            continue
        for word in word_index[first_letter]:
            masked_word = word | mask
            first_missing = (masked_word + 1) & ~masked_word
            while first_missing <= last_start:
                if first_missing not in word_index:
                    first_missing <<= 1
                    continue
                for second_word in word_index[first_missing]:
                    if not (word & second_word):
                        pair = word | second_word
                        if pair in pair_bitset:
                            pair_bitset[pair].add(word)
                        else:
                            pair_bitset[pair] = {word}
                first_missing <<= 1
    return pair_bitset


def index_pairs(pair_list: Sequence[int], progress: Progress) -> dict[int, list[int]]:
    """Returns an index by first|second letter of each pair
    dict[first_letter|second_letter] -> list of pairs"""
    index: dict[int, list[int]] = {
        (a | b): [] for a in LETTERS.values() for b in LETTERS.values() if a != b
    }
    for word in progress.track(pair_list, description="Indexing..."):
        first_bit = (~word + 1) & word
        mask = word ^ first_bit
        second_bit = (~mask + 1) & mask
        index[first_bit | second_bit].append(word)

    return index


# Once we have built the word pairs there are five situations to be considered to be sure we have included all solutions.
#
# Every valid combination contains two pairs and one leftover word but the second pair may use any two of the three
# words available at that point. This means that if we choose any two letters known to be in the final three words
# there must be a pair containing those two letters that may be used to build a solution.
#
# A valid solution uses 25 unique letters so there is always exactly one letter not used.
#
# Scenario 1: the missing letter is "a".
# Choose pair_1 from pairs where the first two letters are "b", "c". Choose pair_2 from pairs where the first
# two letters not in "a"|pair_1 are in pair_2.
#
# Scenario 2: the missing letter is "b".
# Choose pair_1 from pairs where the first two letters are "a", "c". Choose pair_2 from pairs where the first
# two letters not in "b"|pair_1 are in pair_2.
#
# Scenario 3: the missing letter is the first letter not in pair_1 (and not "a","b").
# Choose pair_1 from pairs beginning "a","b". Calculate first, second, third letters not in pair_1.
# Choose pair_2 beginning second,third not in pair_1.
#
# Scenario 4: the missing letter is the second letter not in pair_1 (and not "a","b").
# As for scenario 3 but choose pair_2 beginning first,third not in pair_1.
#
# Scenario 5: the missing letter is not "a", "b", first or second letters not in pair_1 (so all other cases).
# As for scenario 3 but choose pair_2 beginning first,second not in pair_1.
def solve(
    pair_index: dict[int, list[int]],
    valid_solution_pairs: set[int],
    progress: Progress,
) -> set[tuple[int, int]]:
    # Two pairs is a quad?
    quads: set[tuple[int, int]] = set()

    solve_task = progress.add_task("Solving...", total=3)

    # Scenario 1. "a" is not in the solution
    for pair in pair_index[LETTER_B | LETTER_C]:
        masked = pair | 1
        first_other = (masked + 1) & ~masked
        masked |= first_other
        second_other = (masked + 1) & ~masked

        for second_pair in pair_index[first_other | second_other]:
            if (not (pair & second_pair)) and (
                pair | second_pair
            ) in valid_solution_pairs:
                quads.add((pair, second_pair))

    progress.console.log(f"Found {len(quads)} quads")
    progress.update(solve_task, advance=1)

    # Scenario 2. "b" is not in the solution
    for pair in pair_index[LETTER_A | LETTER_C]:
        masked = pair | 2
        first_other = (masked + 1) & ~masked
        masked |= first_other
        second_other = (masked + 1) & ~masked

        for second_pair in pair_index[first_other | second_other]:
            if (not (pair & second_pair)) and (
                pair | second_pair
            ) in valid_solution_pairs:
                quads.add((pair, second_pair))
    progress.console.log(f"Found {len(quads)} quads")
    progress.update(solve_task, advance=1)

    for pair in pair_index[LETTER_A | LETTER_B]:
        masked = pair | 3
        first_other = (masked + 1) & ~masked
        masked = masked | first_other
        second_other = (masked + 1) & ~masked
        masked = masked | second_other
        third_other = (masked + 1) & ~masked

        # Scenario 3: the missing letter is the first letter not in pair_1
        for second_pair in pair_index[second_other | third_other]:
            if (not (pair & second_pair)) and (
                pair | second_pair
            ) in valid_solution_pairs:
                quads.add((pair, second_pair))

        # Scenario 4: the missing letter is the second letter not in pair_1
        for second_pair in pair_index[first_other | third_other]:
            if (not (pair & second_pair)) and (
                pair | second_pair
            ) in valid_solution_pairs:
                quads.add((pair, second_pair))

        # Scenario 5: all other cases
        for second_pair in pair_index[first_other | second_other]:
            if (not (pair & second_pair)) and (
                pair | second_pair
            ) in valid_solution_pairs:
                quads.add((pair, second_pair))

    progress.console.log(f"Found {len(quads)} quads")
    progress.update(solve_task, advance=1)

    return quads


def has_last_word(words: dict[int, object], used_bits: int) -> bool:
    """Given a bitset of 20 letters so only 6 remain unused,
    returns True if there is a word using only unused bits.
    """
    available = used_bits ^ ALL_LETTERS
    bits = available
    while single_bit := ((~bits + 1) & bits):
        if (available & ~single_bit) in words:
            return True
        bits ^= single_bit
    return False


def get_last_word(words: dict[int, set[str]], used_bits: int) -> set[str]:
    """Given a bitset of 20 letters so only 6 remain unused,
    returns True if there is a word using only unused bits.
    """
    available = used_bits ^ ALL_LETTERS
    bits = available
    results: set[str] = set()
    while single_bit := ((~bits + 1) & bits):
        if (available & ~single_bit) in words:
            results |= words[available & ~single_bit]
        bits ^= single_bit
    return results


def reconstruct(
    words: dict[int, set[str]],
    pairs: dict[int, set[int]],
    pair1: int,
    pair2: int,
) -> set[frozenset[str]]:
    words_1 = pairs[pair1]
    first_two_words = {((pair1 & word), (pair1 ^ word)) for word in words_1}
    words_3 = pairs[pair2]
    second_two_words = {((pair2 & word), (pair2 ^ word)) for word in words_3}
    result: set[frozenset[str]] = set()
    for last_word in get_last_word(words, pair1 | pair2):
        for a, b in first_two_words:
            for c, d in second_two_words:
                result |= {
                    frozenset((w1, w2, w3, w4, last_word))
                    for w1 in words[a]
                    for w2 in words[b]
                    for w3 in words[c]
                    for w4 in words[d]
                }
    return result
