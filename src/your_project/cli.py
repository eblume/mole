# -*- coding: utf-8 -*-
import click


@click.command()
def cli():
    """This is your project's primary entry point.

    The general case is that this function will be called by __main__.py, meaning that you can run
    this function from a terminal using the following command (assuming you have done `pip install
    your_package` or `poetry shell` first):

        $ python -m your_package

    The remaining command-line args will be parsed according to the `click` library's semantics. You
    can add decorators to this function to add options and arguments and contexts to this function.
    You can also change this function in to a 'group' and then use it to decorate subcommands. More
    info can be found in click's documentation.

    In general practice, you should keep your code in this module really 'thin'. Just import
    something from your main project space and hand if off for execution. Make your CLI as thin as
    possible, and it will make porting to a new UI easier, and force you to write better code.
    """
    click.echo("Hello World!")
