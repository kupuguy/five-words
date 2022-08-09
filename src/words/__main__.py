from datetime import datetime
from pathlib import Path

import rich
import typer
from rich.progress import Progress, TimeElapsedColumn
from typer import Option

from words.words import (
    index_bitsets,
    index_pairs,
    load_words,
    make_pairs,
    reconstruct,
    solution_masks,
    solve,
)


def main(
    words: Path,
    quiet: bool = Option(
        default=False, help="Output shows stats only not final answer"
    ),
    shard: str = Option(
        default="",
        help="Letter to be used to split the pairs into smaller groups. Longer shard means faster run but more memory",
    ),
) -> None:
    start_time = datetime.now()
    with Progress(*Progress.get_default_columns(), TimeElapsedColumn()) as progress:
        step_task = progress.add_task("Steps...", total=5)
        word_list = load_words(words, progress)
        progress.console.print(f"Loaded {len(word_list):,} words.")
        progress.update(step_task, advance=1)

        word_index = index_bitsets(word_list, progress)
        progress.console.print(f"with {len(word_index)} starting letters")
        progress.update(step_task, advance=1)

        valid_solution_pairs = solution_masks(word_list)

        pair_bitsets = make_pairs(word_index, progress)
        progress.console.print(
            f"Found {sum(len(w) for w in pair_bitsets.values()):,} unique pairs"
        )
        progress.update(step_task, advance=1)

        pair_index = index_pairs(pair_bitsets, shard, progress)

        progress.update(step_task, advance=1)
        quads = solve(pair_index, valid_solution_pairs, shard, progress)
        solutions: set[frozenset[str]] = set()
        for pair, second_pair in quads:
            solutions |= reconstruct(word_list, pair_bitsets, pair, second_pair)

        progress.update(step_task, advance=1)

    if not quiet:
        for solution in solutions:
            rich.print(sorted(solution))
    rich.print(f"Found {len(solutions)} solutions")

    elapsed = datetime.now() - start_time
    rich.print(f"Total elapsed time: [green]{elapsed}[/green]")


if __name__ == "__main__":
    typer.run(main)
