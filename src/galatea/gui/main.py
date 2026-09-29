"""Main entrypoint for launching speedwagon with galatea configured."""

import sys
import argparse

__all__ = []

from typing import Callable, List

GUI_FRONTENDS = ["speedwagon", "table"]


def get_arg_parser() -> argparse.ArgumentParser:
    """Get the argument parser for the galatea gui."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--frontend", default="speedwagon", choices=GUI_FRONTENDS
    )
    return parser


def run_speedwagon_frontend(args=None, main_func=None) -> int:
    if main_func is None:
        from galatea.gui.bootstrap_speedwagon import run_speedwagon  # noqa: PLC0415

        main_func = run_speedwagon

    return main_func(args if args is not None else sys.argv)


def run_table_frontend(argv=None, main_func=None) -> int:
    if main_func is None:
        import galatea.gui.editor  # noqa: PLC0415

        main_func = galatea.gui.editor.main

    return main_func(argv if argv is not None else sys.argv)


def get_frontend(frontend: str) -> Callable[[List[str]], int]:
    match frontend:
        case "speedwagon":

            def speedwagon(argv):
                # HACK: removes --frontend argument because bootstrapping
                #   guis have their own argparse and they will be confused by
                #   this argument.
                if "--frontend=speedwagon" in sys.argv:
                    sys.argv.remove("--frontend=speedwagon")
                return run_speedwagon_frontend(argv)

            return speedwagon

        case "table":

            def table(argv):
                return run_table_frontend(argv)

            return table

        case _:
            raise ValueError(f"Error: Unknown frontend '{frontend}'")


def main(frontend_selector_strategy=get_frontend) -> int:
    """Run the Speedwagon based gui."""
    arg_parser = get_arg_parser()
    args, remaining = arg_parser.parse_known_args()

    try:
        app = frontend_selector_strategy(args.frontend)
        return app(remaining)
    except ImportError:
        print("Error: This feature requires the 'gui' extra.")
        print("Please install it using: pip install 'galatea[gui]'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
