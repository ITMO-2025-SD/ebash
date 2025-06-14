import abc
import dataclasses
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
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
            path_content = ctx.environ["PATH"].split(":")
            if command.startswith(".") or "/" in command:
                path_content.append(".")
            binary_name = None
            for path in path_content:
                fileName = Path(f"{path}/{command}")
                if fileName.is_file():
                    binary_name = fileName.absolute()
                    break

            if binary_name:
                result = subprocess.run([binary_name, *self.args[1:]], capture_output=True, text=True)
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
        if ctx.stdout:  # piped into cat
            return ctx
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
        filename = "(stdin)"
        if ctx.stdout:
            content = "\n".join(x.strip("\n") for x in ctx.stdout)
        else:
            return ctx.with_error(2, "Usage: wc <file>")
    else:
        try:
            filename = args[0]
            with open(args[0], "r") as file:
                content = file.read()
        except FileNotFoundError:
            return ctx.with_error(1, f"Error: File '{args[0]}' not found.")
    lines = content.split("\n")
    words = content.split()
    chars = len(content)
    output = f"{len(lines)}\t{len(words)}\t{chars}\t{filename}"
    return ctx.with_stdout([output])


@CommandRunner.register
def pwd(_args: list[str], ctx: Context):
    return ctx.with_stdout([ctx.workdir])


@CommandRunner.register
def exit(_args: list[str], _ctx: Context):
    sys.exit(0)


@CommandRunner.register
def grep(args: list[str], ctx: Context):
    ignore_case = False
    count = False
    list_files = False
    word = False
    after_context = 0
    i = 0

    # Парсинг опций
    while i < len(args) and args[i].startswith("-"):
        opt = args[i]

        if opt == "-i":
            ignore_case = True
            i += 1
        elif opt == "-c":
            count = True
            i += 1
        elif opt == "-l":
            list_files = True
            i += 1
        elif opt == "-w":
            word = True
            i += 1
        elif opt == "-A":
            if i + 1 >= len(args):
                return ctx.with_error(2, "Option -A requires a number")
            if not args[i + 1].isdigit():
                return ctx.with_error(2, "Invalid number after -A")

            after_context = int(args[i + 1])
            i += 2
        else:
            return ctx.with_error(2, f"Unknown option: {opt}")

    # Проверка паттерна и файлов
    if i >= len(args):
        return ctx.with_error(2, "Usage: grep [options] <pattern> <file>...")

    pattern = args[i]
    files = args[i + 1 :]
    contents: list[str] = []

    if not files:
        if ctx.stdout:  # stdout of last executed command, probably piped into grep
            contents = ctx.stdout
        else:
            return ctx.with_error(2, "Missing file(s)")

    # Компиляция регулярного выражения
    regex = re.escape(pattern)
    if word:
        regex = rf"\b{regex}\b"
    flags = re.IGNORECASE if ignore_case else 0

    try:
        regex = re.compile(regex, flags)
    except re.error as e:
        return ctx.with_error(2, f"Invalid pattern: {e}")

    # Обработка файлов
    out: list[str] = []
    multiple_files = len(files) > 1

    def exec_grep(file: str, lines: list[str]):
        matches = [i for i, line in enumerate(lines) if regex.search(line)]

        # Обработка флагов
        if list_files:
            if matches:
                out.append(file)
            return

        if count:
            count_str = str(len(matches))
            out.append(f"{file}:{count_str}" if multiple_files else count_str)
            return

        # Обработка контекста
        if after_context > 0:
            groups: list[tuple[int, int]] = []

            for m in matches:
                start = m
                end = min(m + after_context, len(lines) - 1)

                if groups and start <= groups[-1][1]:
                    prev_start, _ = groups[-1]
                    groups[-1] = (prev_start, start - 1)
                groups.append((start, end))

            for start, end in groups:
                indicator = ":"
                for line_num in range(start, end + 1):
                    prefix = f"{file}{indicator}" if multiple_files else ""
                    out.append(f"{prefix}{lines[line_num]}")
                    indicator = "-"
        else:
            for line_num in matches:
                prefix = f"{file}:" if multiple_files else ""
                out.append(f"{prefix}{lines[line_num]}")

    for file_ in files:
        try:
            with open(file_, "r") as f:
                lines_ = [line.rstrip("\n") for line in f.readlines()]
        except FileNotFoundError:
            ctx = ctx.with_error(1, f"Error: File '{file_}' not found.")
            continue

        exec_grep(file_, lines_)
    if contents:
        exec_grep("(stdin)", contents)

    return ctx.with_stdout(out)


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
