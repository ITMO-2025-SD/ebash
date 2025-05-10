from typing import final, override

from ebash_lib.common.command import CommandRunner, MetaCommand, Pipe
from ebash_lib.common.context import Context
from ebash_lib.common.parser import PrefixParser, SimpleParser, SplittingParser


def test_simple_parser():
    parser = SimpleParser[MetaCommand](CommandRunner)
    assert parser.parse_string("bash -c pain") == CommandRunner(["bash", "-c", "pain"])
    assert parser.parse_string("bash -c 'long command'") == CommandRunner(["bash", "-c", "long command"])
    assert parser.parse_string("") is None


def test_splitting():
    parser = SimpleParser[MetaCommand](CommandRunner).chain(SplittingParser, Pipe, "|")
    assert parser.parse_string("bash -c pain") == CommandRunner(["bash", "-c", "pain"])
    assert parser.parse_string("cat | echo") == Pipe([CommandRunner(["cat"]), CommandRunner(["echo"])])
    assert parser.parse_string("echo 'a | b' | echo") == Pipe(
        [CommandRunner(["echo", "a | b"]), CommandRunner(["echo"])]
    )
    assert parser.parse_string("not | closed | pipe |") is None


def test_setenv():
    # Simpler test because SetEnvData.parse is not written
    def check_string(token: str):
        try:
            return int(token)
        except ValueError:
            return None

    @final
    class WithNumbers(MetaCommand):
        def __init__(self, command: MetaCommand, results: list[int]):
            self.command = command
            self.results = results

        @override
        def __call__(self, ctx: Context) -> Context:
            raise NotImplementedError("WithBool")

        @override
        def __eq__(self, value: object, /) -> bool:
            return isinstance(value, WithNumbers) and value.command == self.command and value.results == self.results

    parser = SimpleParser[MetaCommand](CommandRunner).chain(PrefixParser, WithNumbers, check_string)
    assert parser.parse_string("bash -c pain") == CommandRunner(["bash", "-c", "pain"])
    assert parser.parse_string("1 2 345 bash") == WithNumbers(CommandRunner(["bash"]), [1, 2, 345])
    assert parser.parse_string("1 2 345 6") is None


def test_priority():
    parser = (
        SimpleParser[MetaCommand](CommandRunner).chain(SplittingParser, Pipe, "|").chain(SplittingParser, Pipe, "&")
    )
    # (a | b) & c
    assert parser.parse_string("a | b & c") == Pipe(
        [Pipe([CommandRunner(["a"]), CommandRunner(["b"])]), CommandRunner(["c"])]
    )
    # a & (b | c)
    assert parser.parse_string("a & b | c") == Pipe(
        [CommandRunner(["a"]), Pipe([CommandRunner(["b"]), CommandRunner(["c"])])]
    )
