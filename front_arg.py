#!/usr/bin/env python3

import click
import time
from pathlib import Path
from tabulate import tabulate

from backend import Backend
from filehandler import FileHandler
from containers import *


@click.group()
def main():
    pass


@main.group()
def inwards():
    pass


@inwards.command()
@click.option("--user")
def overview(user: str):
    if user is not None:
        print(FileHandler.server_overview_of(user.encode("ascii", "replace")))
    else:
        print(FileHandler.server_storage_status())


def wait_and_print_overviews(backend: Backend) -> None:
    print("Loading...", end=" ", flush=True)
    time.sleep(1)
    print("Done. Your overviews:\n")
    overviews = backend.get_overviews()
    if len(overviews) > 0:
        print(tabulate(overviews, headers="keys"))
    else:
        print("No overviews had been received.")
    print()


@main.group(invoke_without_command=True)
@click.option("--username", prompt=True)
@click.option("--debug", is_flag=True)
@click.pass_context
def outwards(ctx, username, debug):
    ctx.obj = Backend(username, debug=debug)
    wait_and_print_overviews(ctx.obj)


@outwards.command()
def listen():
    while True:
        time.sleep(0.33)


@outwards.command()
@click.pass_obj
def who_around(backend: Backend):
    backend.out_status_broadcast()
    wait_and_print_overviews(backend)

@outwards.command()
@click.argument("filepath", type=Path)
@click.argument("to_who")
@click.pass_obj
def upload(backend: Backend, filepath: Path, to_who: str):
    agent = AgentHandler.get_agent(to_who.encode("ascii", "replace"))
    if agent is None:
        print(f"No such agent with name '{to_who}' is found.")
    else:
        with open(filepath, "r") as f:
            data = f.read(30)
        print(f"Uploading file {filepath.name} to '{to_who}' with data like:\n{ data }...")
        if not backend.out_upload(agent, filepath):
            print("Not successful!")
    print()


@outwards.command()
@click.argument("filename")
@click.argument("from_who")
@click.argument("where", type=Path)
@click.pass_obj
def download(backend: Backend, filename: str, from_who: str, where: Path):
    agent = AgentHandler.get_agent(from_who.encode("ascii", "replace"))
    if agent is None:
        print(f"No such agent with name '{from_who}' is found.")
    else:
        pass
    print()


if __name__ == "__main__":
    main()
