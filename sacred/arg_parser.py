#!/usr/bin/env python
# coding=utf-8
from __future__ import division, print_function, unicode_literals
import ast
from collections import OrderedDict
import textwrap
import sys
import inspect
from docopt import docopt

from sacred.commandline_options import gather_command_line_options
from sacred.commands import help_for_command
from sacred.utils import set_by_dotted_path

__sacred__ = True  # marks files that should be filtered from stack traces

__all__ = ('parse_args', 'get_config_updates')


USAGE_TEMPLATE = """Usage:
  {program_name} help [COMMAND]
  {program_name} (-h | --help)
  {program_name} [(with UPDATE...)] [options]
  {program_name} COMMAND [(with UPDATE...)] [options]

{description}

Options:
{options}

Arguments:
  COMMAND   Name of command to run (see below for list of commands)
  UPDATE    Configuration assignments of the form foo.bar=17
{arguments}
{commands}"""


def parse_args(argv, description="", commands=None, print_help=True):
    options = gather_command_line_options()
    usage = _format_usage(argv[0], description, commands, options)
    args = docopt(usage, [str(a) for a in argv[1:]], help=print_help)
    if not args['help'] or not print_help:
        return args

    if args['COMMAND'] is None:
        print(usage)
        sys.exit()
    else:
        print(help_for_command(commands[args['COMMAND']]))
        sys.exit()


def get_config_updates(updates):
    config_updates = {}
    named_configs = []
    if not updates:
        return config_updates, named_configs
    for upd in updates:
        if upd == '':
            continue
        path, sep, value = upd.partition('=')
        if sep == '=':
            path = path.strip()    # get rid of surrounding whitespace
            value = value.strip()  # get rid of surrounding whitespace
            set_by_dotted_path(config_updates, path, _convert_value(value))
        else:
            named_configs.append(path)
    return config_updates, named_configs


def _format_options_usage(options):
    options_usage = ""
    for op in options:
        short, long = op.get_flag()
        if op.arg:
            flag = "-{short} {arg} --{long}={arg}".format(
                short=short, long=long, arg=op.arg)
        else:
            flag = "-{short} --{long}".format(short=short, long=long)

        wrapped_description = textwrap.wrap(inspect.cleandoc(op.__doc__),
                                            width=79,
                                            initial_indent=' ' * 32,
                                            subsequent_indent=' ' * 32)
        wrapped_description = "\n".join(wrapped_description).strip()

        options_usage += "  {0:28}  {1}\n".format(flag, wrapped_description)
    return options_usage


def _format_arguments_usage(options):
    argument_usage = ""
    for op in options:
        if op.arg and op.arg_description:
            wrapped_description = textwrap.wrap(op.arg_description,
                                                width=79,
                                                initial_indent=' ' * 12,
                                                subsequent_indent=' ' * 12)
            wrapped_description = "\n".join(wrapped_description).strip()
            argument_usage += "  {0:8}  {1}\n".format(op.arg,
                                                      wrapped_description)
    return argument_usage


def _format_command_usage(commands):
    if not commands:
        return ""
    command_usage = "\nCommands:\n"
    cmd_len = max([len(c) for c in commands] + [8])
    command_doc = OrderedDict(
        [(cmd_name, _get_first_line_of_docstring(cmd_doc))
         for cmd_name, cmd_doc in commands.items()])
    for cmd_name, cmd_doc in command_doc.items():
        command_usage += ("  {:%d}  {}\n" % cmd_len).format(cmd_name, cmd_doc)
    return command_usage


def _format_usage(program_name, description, commands=None, options=()):
    usage = USAGE_TEMPLATE.format(
        program_name=program_name,
        description=description.strip() if description else '',
        options=_format_options_usage(options),
        arguments=_format_arguments_usage(options),
        commands=_format_command_usage(commands)
    )
    return usage


def _get_first_line_of_docstring(func):
    return textwrap.dedent(func.__doc__ or "").strip().split('\n')[0]


def _convert_value(value):
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        # use as string if nothing else worked
        return value
