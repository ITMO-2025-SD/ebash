import os

from ebash_lib.bash_core import BashLoop
from ebash_lib.bash_parser import BashParser


def main():
    bash = BashLoop(BashParser, dict(os.environ), os.getcwd())
    bash.run()


if __name__ == "__main__":
    main()
