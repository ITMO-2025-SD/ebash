import abc
from collections.abc import Iterable


class Command(abc.ABC):
    """Текстовая команда, например Cat."""

    @abc.abstractmethod
    def __call__(self, args: Iterable[str], stdin: Iterable[str]) -> Iterable[str]: ...

    @classmethod
    @abc.abstractmethod
    def getName(cls): ...


class Cat(Command): ...


class Echo(Command): ...


class Context:
    stdin: Iterable[str]
    env: dict[str, str]


Context(stdin=[stdout], env={**old_context.env, x="abc"})


class BashCommand(abc.ABC):
    """Мета-команда Bash, например Pipe или And."""

    @abc.abstractmethod
    def __call__(self, ctx: Context) -> Context: ...

    @classmethod
    @abc.abstractmethod
    # не уверен, что здесь проще всего так сделать, надо будет поправить
    def parse[T: "BashCommand"](
        cls: type[T], remaining: "list[type[BashCommand]]", data: list[str]
    ) -> T: ...


class CommandCaller(BashCommand):
    def __init__(self, parameters: list[str]):
        self.cmd = selectCommand(parameters[0])
        self.args = parameters[1:]

    def __call__(self, stdin: Iterable[str]):
        return self.cmd(self.args, stdin)

    @classmethod
    def parse(
        cls, remaining: list[type[BashCommand]], data: list[str]
    ) -> "CommandCaller":
        return CommandCaller(data)


# Такая идея для регистрации команд
# CommandCaller.setDefault(Subprocess)
# CommandCaller.register(Cat)


class Pipe(BashCommand):
    def __init__(self, commands: list[BashCommand]):
        self.commands = commands

    def __call__(self, context: Context):
        for command in self.commands:
            context = command(context)
        return context

    @classmethod
    def parse(cls, remaining: list[type[BashCommand]], data: list[str]) -> "Pipe":
        # тупой способ, надо поправить
        return Pipe(
            [
                remaining[0].parse(remaining[1:], x.split())
                for x in " ".join(data).split(" | ")
            ]
        )


class Bash:
    def __init__(self, commands, parser):
        self.parser = parser(commands)

    def process(self, cmd: str) -> Iterable[str]:
        tree = self.parser.parse(cmd)
        return self.commands[tree.type](tree)


# парсер пока не написан
bash = Bash(Parser([CommandCaller, Pipe, And]))
while True:
    print("\n".join(bash.process(input())))
