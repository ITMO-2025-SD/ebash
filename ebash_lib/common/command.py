import abc
import dataclasses
from collections.abc import Iterable
from typing import final, override

from ebash_lib.common.context import Context


class MetaCommand(abc.ABC):
    @abc.abstractmethod
    def __call__(self, ctx: Context) -> Context: ...


@final
class CommandRunner(MetaCommand):
    def __init__(self, args: list[str]):
        self.args = args

    @override
    def __call__(self, ctx: Context) -> Context:
        raise NotImplementedError("CommandRunner")

    @override
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, CommandRunner) and value.args == self.args


@final
class Pipe(MetaCommand):
    def __init__(self, chain: Iterable[MetaCommand]):
        self.chain = chain

    @override
    def __call__(self, ctx: Context) -> Context:
        raise NotImplementedError("Pipe")

    @override
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, Pipe) and value.chain == self.chain


@dataclasses.dataclass
class SetEnvData:
    name: str
    value: str

    @classmethod
    def parse(cls, _token: str) -> "SetEnvData | None":
        raise NotImplementedError("SetEnvData")


@final
class SetEnv(MetaCommand):
    def __init__(self, command: MetaCommand, env_vars: list[SetEnvData]):
        self.command = command
        self.env_vars = env_vars

    @override
    def __call__(self, ctx: Context) -> Context:
        raise NotImplementedError("SetEnv")

    @override
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, SetEnv) and value.command == self.command and value.env_vars == self.env_vars
