import abc
import shlex
from typing import Callable, Concatenate, Self, final, override


class Parser[M](abc.ABC):
    @abc.abstractmethod
    def parse(self, tokens: list[str]) -> M | None:
        """Receives a list of tokens, should return a command, or None if the syntax is invalid."""

    def parse_string(self, data: str):
        return self.parse(shlex.split(data))

    # Fluent syntax for parser upgrades
    def chain[**P, T](self, constructor: Callable[Concatenate[Self, P], T], *args: P.args, **kwargs: P.kwargs) -> T:
        return constructor(self, *args, **kwargs)


def split_list[T](value: T, lst: list[T]) -> list[list[T]]:
    result: list[list[T]] = []
    current: list[T] = []
    for item in lst:
        if item == value:
            result.append(current)
            current = []
        else:
            current.append(item)
    result.append(current)
    return result


@final
class SimpleParser[M](Parser[M]):
    def __init__(self, constructor: Callable[[list[str]], M]) -> None:
        super().__init__()
        self.constructor = constructor

    @override
    def parse(self, tokens: list[str]) -> M | None:
        if not tokens:
            return None
        return self.constructor(tokens)


@final
class SplittingParser[M](Parser[M]):
    def __init__(self, parser: Parser[M], constructor: Callable[[list[M]], M], split_by: str) -> None:
        super().__init__()
        self.constructor = constructor
        self.subparser = parser
        self.split_by = split_by

    @override
    def parse(self, tokens: list[str]) -> M | None:
        tokens_split = split_list(self.split_by, tokens)
        if len(tokens_split) <= 1:
            return self.subparser.parse(tokens)

        results: list[M] = []
        for block in tokens_split:
            if result := self.subparser.parse(block):
                results.append(result)
            else:
                return None
        return self.constructor(results)


@final
class PrefixParser[T, M](Parser[M]):
    def __init__(
        self,
        parser: Parser[M],
        constructor: Callable[[M, list[T]], M],
        prefix_checker: Callable[[str], T | None],
    ) -> None:
        super().__init__()
        self.constructor = constructor
        self.subparser = parser
        self.checker = prefix_checker

    @override
    def parse(self, tokens: list[str]) -> M | None:
        prefix: list[T] = []
        for i, tok in enumerate(tokens):
            if (result := self.checker(tok)) is not None:
                prefix.append(result)
            else:
                break
        else:  # Break was never called
            return None

        result = self.subparser.parse(tokens[i:])
        if prefix and result:
            result = self.constructor(result, prefix)
        return result
