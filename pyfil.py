#!/usr/bin/env python3
"""
Use python as a filter on stdin. If the expression iterator, print
each item on its own line. If the value is a builtin container type,
attempt to serialize it as json before printing.

pyfil automatically imports any modules used in expressions.

If you'd like to create any other objects to use in the execution
environment ~/.config/pyfil-env.py and put things in it.

default objects:

    l = []
    d = {}

These are empty containers you might wish to add items to during
iteration, for example.

x is always the return value of the previous expression unless --exec.

The execution environment also has a special object for stdin,
creatively named "stdin". This differs from sys.stdin in that it
removes trailing newlines when you iterate over it, and it has
a property, stdin.l, which returns a list of the lines, rather than an
iterator.

Certain other flags; --loop (or anything that implies --loop), --json,
--split or --field_sep; may create additional objects. Check the flag
descriptions for further details.

Home: https://github.com/ninjaaron/pyfil
"""
import collections
import sys
import json
import os
import re
import ast
import argparse
from functools import update_wrapper, partial
from typing import Iterable, Callable, Iterator


class LazyDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setattr__
    __delattr__ = dict.__delitem__  # type: ignore


class reify:
    """"stolen" from Pylons"""

    def __init__(self, wrapped):
        self.wrapped = wrapped
        update_wrapper(self, wrapped)

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


class NameSpace(dict):
    """namespace that imports modules lazily."""

    def __missing__(self, name):
        try:
            return __import__(name)
        except ImportError:
            raise NameError("name '{}' is not defined".format(name))


class StdIn:
    """class for wrapping sys.stdin"""

    def __init__(self):
        self.lines = (line.rstrip("\n") for line in sys.stdin)

    def __iter__(self):
        return self.lines

    @reify
    def l(self):  # noqa: E743, E741
        return sys.stdin.read().splitlines()

    def __next__(self):
        return next(self.lines)

    def __getattr__(self, name):
        return getattr(sys.stdin, name)


class SafeList(collections.UserList):
    "class for getting fields from stdin without raising errors"

    def __getitem__(self, index):
        try:
            return self.data[index]
        except IndexError:
            return ""

    def __iter__(self):
        return iter(self.data)


def handle_errors(e: Exception, args):
    """stupid simple error handling"""
    if args.raise_errors:
        raise e
    elif args.silence_errors:
        pass
    else:
        print(
            "\x1b[31m{}\x1b[0m:".format(e.__class__.__name__),
            e,
            file=sys.stderr,
        )


class SafeListEncode(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, SafeList):
            return obj.data
        return json.JSONEncoder.default(self, obj)


def print_obj(obj, indent=None):
    """print strings, serialize other stuff to json, or don't"""
    if isinstance(obj, str):
        print(obj)
    else:
        try:
            print(
                json.dumps(
                    obj, ensure_ascii=False, indent=indent, cls=SafeListEncode
                )
            )
        except TypeError:
            print(obj)


def parse_handler(handler: str):
    exn, expr = map(str.strip, handler.split(":", maxsplit=1))
    return getattr(__builtins__, exn), expr


def run_with_exception_handler(
    func: Callable, exception, handler: str, expr: str,
):
    try:
        return func(expr)
    except exception:
        return func(handler)


def run_expressions(runner, expressions, namespace, args):
    value = None
    for expr in expressions:
        try:
            value = runner(expr)
        except Exception as e:
            handle_errors(e, args)
            continue

        if not args.exec:
            namespace.update(x=value)
    return value


def display_value(value, args):
    if args.join is not None and isinstance(value, Iterable):
        joiner = "'''" + args.join.replace("'", r"\'") + "'''"
        print(ast.literal_eval(joiner).join(map(str, value)))
    elif value is None:
        pass
    elif isinstance(value, Iterator):
        for i in value:
            print_obj(i)
    else:
        indent = None if (args.loop or args.force_oneline_json) else 2
        print_obj(value, indent)


def run(expressions: Iterable[str], args, namespace, run_expression: Callable):
    value = run_expressions(run_expression, expressions, namespace, args)
    if not (args.quiet or args.exec):
        display_value(value, args)


def get_args(arguments=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add = parser.add_argument

    add(
        "expression",
        nargs="+",
        help="expression(s) to be "
        "executed. If multiple expression arguments are given, "
        "and --exec is not used, the value of the previous "
        "expression is available as 'x' in the following "
        "expression. if --exec is used, all assignment must be "
        "explicit.",
    )

    add(
        "-l",
        "--loop",
        action="store_true",
        help="for n, i in enumerate(stdin): expressions",
    )

    add(
        "-x",
        "--exec",
        action="store_true",
        help="use exec instead of eval. statements are allowed, "
        "but automatic printing is lost. doesn't affect --post",
    )

    add(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress automatic printing. doesn't affect --post",
    )

    add(
        "-j",
        "--json",
        action="store_true",
        help="load stdin as json into object 'j'; If used with "
        "--loop, treat each line of stdin as a new object",
    )

    add(
        "-J",
        "--real-dict-json",
        action="store_true",
        help="like -j, but creates real dictionaries instead of "
        "the wrapper that allows dot syntax.",
    )

    add(
        "-o",
        "--force-oneline-json",
        action="store_true",
        help="outside of loops and iterators, objects serialzed "
        "to json print with two-space indent. this forces "
        "this forces all json objects to print on a single "
        "line.",
    )

    add(
        "-b",
        "--pre",
        help="statement to evaluate before expression args. "
        "multiple statements may be combined with ';'. "
        "no automatic printing",
    )

    add(
        "-e",
        "--post",
        help="expression to evaluate after the loop. always "
        "handeled by eval, even if --exec, and always prints "
        "return value, even if --quiet. implies --loop",
    )

    add(
        "-s",
        "--split",
        action="store_true",
        help="split lines from stdin on whitespace into list 'f'. implies --loop",
    )

    add(
        "-F",
        "--field-sep",
        metavar="PATTERN",
        help="regex used to split lines from stdin into list 'f'. implies --loop",
    )

    add(
        "-n",
        "--join",
        metavar="STRING",
        help="join items in iterables with STRING",
    )

    add(
        "-R",
        "--raise-errors",
        action="store_true",
        help="raise errors in evaluation and stop execution "
        "(default: print message to stderr and continue)",
    )

    add(
        "-S",
        "--silence-errors",
        action="store_true",
        help="suppress error messages",
    )

    add(
        "-H",
        "--exception-handler",
        help="specify exception handler with the format "
        "'Exception: alternative expression to eval'",
    )

    return parser.parse_args(arguments)


def main():
    args = get_args()
    func = "exec" if args.exec else "eval"
    expressions = [
        compile(e if args.exec else "(%s)" % e, "<string>", func)
        for e in args.expression
    ]
    user_env = os.environ["HOME"] + "/.config/pyfil-env.py"

    namespace = NameSpace(__builtins__)
    namespace.update(stdin=StdIn(), l=[], d={})
    if os.path.exists(user_env):
        exec(open(user_env).read(), namespace)

    if args.json:
        jdecode = json.JSONDecoder(object_hook=LazyDict).decode
    elif args.real_dict_json:
        jdecode = json.loads
        args.json = True

    if args.post or args.split or args.field_sep:
        args.loop = True
    
    _evaluate = exec if args.exec else eval
    evaluate = lambda expr: _evaluate(expr, namespace)

    if args.exception_handler:
        exception, handler = parse_handler(args.exception_handler)
        run_expression = partial(
            run_with_exception_handler, evaluate, exception, handler
        )
    else:
        run_expression =  evaluate

    if args.loop:
        if args.pre:
            exec(args.pre, namespace)
        for n, i in enumerate(map(str.rstrip, sys.stdin)):
            namespace.update(i=i, n=n)
            if args.json:
                namespace.update(j=jdecode(i))

            if args.field_sep:
                if len(args.field_sep) == 1:
                    f = SafeList(i.split(args.field_sep))
                else:
                    f = SafeList(re.split(args.field_sep, i))
                namespace.update(f=f)
            elif args.split:
                namespace.update(f=SafeList(i.split()))

            run(expressions, args, namespace, run_expression)
        if args.post:
            if args.quiet or args.exec:
                args.loop, args.quiet, args.exec = None, None, None
                _evaluate = eval
            run(("(%s)" % args.post,), args, namespace, run_expression)

    else:
        if args.pre:
            exec(args.pre, namespace)
        if args.json:
            namespace.update(j=jdecode(sys.stdin.read()))
        run(expressions, args, namespace, run_expression)


if __name__ == "__main__":
    main()
