# Copyright 2018 Canonical Ltd.
# Licensed under the LGPLv3, see LICENCE.txt file for details.

"""Main entry point for the application commands."""

from functools import partial
import sys

from . import (
    _exceptions,
    _fsteal,
)


def main(command):
    """Set up and run the given command.

    The provided command is an object implementing the following interface:
        - setup() -> args: for parsing command line arguments;
        - run(args): for executing the command, possibly raising AppError.
    """
    args = command.setup()
    try:
        command.run(args)
    except KeyboardInterrupt:
        print('exiting')
        sys.exit(1)
    except _exceptions.AppError as err:
        sys.exit(err)


fsteal = partial(main, _fsteal)
