#!/usr/bin/env python3

import click

from backend import *


@click.group()
def main():
    pass


@main.group()
def loopback():
    print("Inside loopback")


@main.group()
def network():
    print("Inside network")


@network.command()
@click.option("--from_who", type=str)
def status(from_who: str):
    if from_who is not None:
        print("Getting from:", from_who)
    else:
        print("Getting it from everyone.")


if __name__ == "__main__":
    main()
