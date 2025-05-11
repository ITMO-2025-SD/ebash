import abc
import dataclasses
from collections.abc import Iterable
from typing import final, override
import os
import sys
from ebash_lib.common.context import Context


class MetaCommand(abc.ABC):
    @abc.abstractmethod
    def __call__(self, ctx: Context) -> Context: ...




class CommandRunner:
    def __init__(self, args: list[str]):
        self.args = args

    @override
    def __call__(self, ctx: dict) -> dict:
        if not self.args:
            return ctx

        command = self.args[0]

        if command == "echo":
            print(" ".join(self.args[1:]))

        elif command == "cat":
            if len(self.args) < 2:
                print("Usage: cat <file>")
            else:
                try:
                    with open(self.args[1], 'r') as file:
                        print(file.read())
                except FileNotFoundError:
                    print(f"Error: File '{self.args[1]}' not found.")

        elif command == "wc":
            if len(self.args) < 2:
                print("Usage: wc <file>")
            else:
                try:
                    with open(self.args[1], 'r') as file:
                        content = file.read()
                        lines = content.split('\n')
                        words = content.split()
                        chars = len(content)
                        print(f"{len(lines)} {len(words)} {chars} {self.args[1]}")
                except FileNotFoundError:
                    print(f"Error: File '{self.args[1]}' not found.")

        elif command == "pwd":
            print(os.getcwd())

        elif command == "exit":
            sys.exit(0)

        elif command == "grep":
            if len(self.args) < 3:
                print("Usage: grep <pattern> <file>")
            else:
                try:
                    with open(self.args[2], 'r') as file:
                        for line in file:
                            if self.args[1] in line:
                                print(line.strip())
                except FileNotFoundError:
                    print(f"Error: File '{self.args[2]}' not found.")

        else:
            raise NotImplementedError(f"Command '{command}' not supported.")

        return ctx

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
