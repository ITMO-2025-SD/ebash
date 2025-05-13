import abc
import dataclasses
import sys
import subprocess
from pathlib import Path
from collections.abc import Iterable
from typing import Callable, ClassVar, final, override

from ebash_lib.common.context import Context


class MetaCommand(abc.ABC):
    @abc.abstractmethod
    def __call__(self, ctx: Context) -> Context: ...


@final
class CommandRunner(MetaCommand):
    registered_commands: ClassVar[dict[str, Callable[[list[str], Context], Context]]] = {}

    @classmethod
    def register(cls, command: Callable[[list[str], Context], Context]):
        cls.registered_commands[command.__name__] = command
        return command

    def __init__(self, args: list[str]):
        # args is never empty
        self.args = args

    @override
    def __call__(self, ctx: Context) -> Context:
        command = self.args[0]

        if command in self.registered_commands:
            return self.registered_commands[command](self.args[1:], ctx)
        else:
            pathContent = ctx.environ["PATH"].split(":")
            binaryName = None
            for path in pathContent:
                fileName = Path(f"{path}/{command}")
                if fileName.is_file():
                    binaryName = fileName
                    break

            if binaryName:
                result = subprocess.run([binaryName, *self.args[1:]], capture_output=True, text=True)
                if result.stderr:
                    return ctx.with_error(result.returncode, result.stderr)
                elif result.stdout:
                    return ctx.with_stdout((result.stdout).split("\n"))
                else:
                    return ctx
                
            return ctx.with_stdout([f"Command '{command}' not found"])

    @override
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, CommandRunner) and value.args == self.args


@CommandRunner.register
def echo(args: list[str], ctx: Context):
    return ctx.with_stdout([" ".join(args)])


@CommandRunner.register
def cat(args: list[str], ctx: Context):
    if len(args) < 1:
        return ctx.with_error(2, "Usage: cat <file>")
    else:
        try:
            with open(args[0], "r") as file:
                return ctx.with_stdout([x.strip() for x in file.readlines()])
        except FileNotFoundError:
            return ctx.with_error(1, f"Error: File '{args[0]}' not found.")


@CommandRunner.register
def wc(args: list[str], ctx: Context):
    if len(args) < 1:
        return ctx.with_error(2, "Usage: wc <file>")
    else:
        try:
            with open(args[0], "r") as file:
                content = file.read()
                lines = content.split("\n")
                words = content.split()
                chars = len(content)
                output = f"{len(lines)}\t{len(words)}\t{chars}\t{args[0]}"
                return ctx.with_stdout([output])
        except FileNotFoundError:
            return ctx.with_error(1, f"Error: File '{args[0]}' not found.")


@CommandRunner.register
def pwd(_args: list[str], ctx: Context):
    return ctx.with_stdout([ctx.workdir])


@CommandRunner.register
def exit(_args: list[str], _ctx: Context):
    sys.exit(0)


@CommandRunner.register
def grep(args: list[str], ctx: Context):
    if len(args) < 2:
        return ctx.with_error(2, "Usage: grep <pattern> <file>")
    else:
        out: list[str] = []
        try:
            with open(args[1], "r") as file:
                for line in file:
                    if args[0] in line:
                        out.append(line)
            return ctx.with_stdout(out)
        except FileNotFoundError:
            return ctx.with_error(1, f"Error: File '{args[1]}' not found.")


@final
class Pipe(MetaCommand):
    def __init__(self, chain: Iterable[MetaCommand]):
        self.chain = chain

    @override
    def __call__(self, ctx: Context) -> Context:
        current_ctx = ctx
        for command in self.chain:
            current_ctx = command(current_ctx)
            if current_ctx.return_code != 0:
                return current_ctx
        return current_ctx

    @override
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, Pipe) and value.chain == self.chain


@dataclasses.dataclass
class SetEnvData:
    name: str
    value: str

    @classmethod
    def parse(cls, token: str) -> "SetEnvData | None":
        if "=" in token:
            return SetEnvData(*token.split("=", 1))
        return None


@final
class SetEnv(MetaCommand):
    def __init__(self, command: MetaCommand | None, env_vars: list[SetEnvData]):
        self.command = command
        self.env_vars = env_vars

    @override
    def __call__(self, ctx: Context) -> Context:
        new_environ = dict(ctx.environ)
        for var in self.env_vars:
            new_environ[var.name] = var.value
        new_ctx = ctx.with_environ(new_environ)
        if not self.command:
            return new_ctx
        new_ctx2 = self.command(new_ctx)
        return new_ctx2.with_environ(ctx.environ)

    @override
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, SetEnv) and value.command == self.command and value.env_vars == self.env_vars
