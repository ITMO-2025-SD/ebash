import pytest
from pathlib import Path
from ebash_lib.common.command import CommandRunner, cd, ls
from ebash_lib.common.context import Context


@pytest.fixture
def initial_context():
    return Context(
        workdir=str(Path.home()),
        environ={"PATH": "/usr/bin:/bin"},
        return_code=0,
        stdout=[],
        stderr=""
    )


def test_cd_basic(initial_context):
    test_dir = "/tmp"
    ctx = cd([test_dir], initial_context)
    assert ctx.workdir == test_dir

    pwd_ctx = CommandRunner(["pwd"])(ctx)
    assert pwd_ctx.stdout[0] == test_dir


def test_cd_home(initial_context):
    home = str(Path.home())
    ctx = cd([], initial_context)
    assert ctx.workdir == home


def test_cd_relative(initial_context):
    start_dir = "/tmp"
    ctx = initial_context.with_dir(start_dir)

    test_dir = "/tmp/test_cd_dir"
    Path(test_dir).mkdir(exist_ok=True)

    try:
        ctx = cd(["test_cd_dir"], ctx)
        assert ctx.workdir == test_dir

        ctx = cd([".."], ctx)
        assert ctx.workdir == start_dir
    finally:
        Path(test_dir).rmdir()


def test_ls_pattern(initial_context):
    test_dir = "/tmp"
    ctx = initial_context.with_dir(test_dir)

    test_files = ["ls_test_file1", "ls_test_file2", "other_file"]
    for f in test_files:
        (Path(test_dir) / f).touch()

    try:
        ctx = ls(["ls_test_file*"], ctx)
        assert sorted(ctx.stdout) == sorted(["ls_test_file1", "ls_test_file2"])

        ctx = ls([f"{test_dir}/ls_test_file*"], initial_context)
        assert sorted(ctx.stdout) == sorted(["ls_test_file1", "ls_test_file2"])
    finally:
        for f in test_files:
            (Path(test_dir) / f).unlink(missing_ok=True)
