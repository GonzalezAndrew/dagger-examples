import sys
import anyio
import dagger

import argparse

async def concurrent_tests():
    """this job runs our tests against diff python versions concurrently!"""
    versions = ["3.7", "3.8", "3.9", "3.10", "3.11"]

    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        # get reference to the local project
        src = client.host().directory(".")

        async def test_version(version: str):
            python = (
                client.container().from_(f"python:{version}-slim-buster")
                # mount cloned repository into image
                .with_mounted_directory("/src", src)
                # set current working directory for next commands
                .with_workdir("/src")
                .with_exec(["pip", "install", "--upgrade", "pip"])
                # install test dependencies
                .with_exec(["pip", "install", "-r", "requirements.txt"])
                # run tests
                .with_exec(["pytest", "tests"])
            )

            print(f"Starting tests for Python {version}")

            # execute
            await python.exit_code()

            print(f"Tests for Python {version} succeeded!")

        # when this block exits, all tasks will be awaited (i.e., executed)
        async with anyio.create_task_group() as tg:
            for version in versions:
                tg.start_soon(test_version, version)

    print("All tasks have finished")

async def simple_test():
    """this job runs a single simple pytest against our module"""
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        # get reference to the local python project
        src = client.host().directory(".")

        # lets configure our build environment
        python = (
            client.container()
            .from_("python:3.10.9-slim-buster") # the image where we will be running our job
            .with_mounted_directory("/src", src) # mount the repo into the image
            .with_workdir("/src") # set working dir to the local project
            .with_exec(["pip", "install", "--upgrade", "pip"]) 
            .with_exec(["pip", "install", '-r', "requirements.txt"]) # install all deps
            .with_exec(["pytest", "tests/"]) # run tests
        )

        # execute the above job
        await python.exit_code()

    print('Test succeeded!!')

def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="dagger",
        description="A command line tool to run dagger pipelines.",
    )

    subparser = parser.add_subparsers(dest="command")

    simple_parser = subparser.add_parser(
        "simple",
        help="Run our simple pipeline."
    )

    concurrent_parser = subparser.add_parser(
        "concurrent",
        help="Run our concurrent pipeline."
    )

    help = subparser.add_parser("help", help="Show the help for a specific command.")
    help.add_argument("help_cmd", nargs="?", help="Command to show help for.")

    if len(argv) == 0:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    if args.command == "help" and args.help_cmd:
        parser.parse_args([args.help_cmd, "--help"])
        return 0
    elif args.command == "help":
        parser.parse_args(["--help"])
        return 0

    if args.command == "simple":
        return anyio.run(simple_test)
    if args.command == "concurrent":
        return anyio.run(concurrent_tests)
    else:
        raise NotImplementedError(f"The command {args.command} is not implemented!")


if __name__ == "__main__":
    main()