#!/usr/bin/env python3

import click

from backend import Backend


@click.group()
def main():
    pass


@main.command()
@click.option("--from_who", type=str)
def status(from_who: str):
    b = Backend()
    if from_who is not None:
        print("Getting from:", from_who)
    else:
        print("Getting it from everyone.")


if __name__ == "__main__":
    main()
