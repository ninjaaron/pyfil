#!/usr/bin/env python3
'''
------------------------------------------------------------------------
Evaluate python expressions. Print the return value. If the return value
is an iterator, print each item on its own line.

available objects
-----------------
Automatically imports (unless overridden in ~/.config/pyfil-env.py):
    sys, os, re, math, pprint from pprint, timeit from timeit and
    strftime from time.

If you'd like to specify a custom execution environment for rep, create
~/.config/pyfil-env.py and put things in it.

The execution environment also has a special object for stdin,
creatively named `stdin`. This differs from sys.stdin in that it rstrips
(aka chomps) all the lines when you iterate over it, and it has a
property, stdin.l, which returns a list of the (rstripped) lines. pyfil
is quite bullish about using rstrip because python's print function will
supply an additional newline, and if you just want the value of the text
in the line, you almost never want the newline character. If you do want
the newlines, access sys.stdin directly.

stdin inherits the rest of its methods from sys.stdin, so you can use
stdin.read() to get a string of all lines, if that's what you need.

looping over stdin
------------------
one can do simple loops with a generator expression:

    $ ls / | rep '(i.upper() for i in stdin)'
    BIN@
    BOOT/
    DEV/
    ETC/
    HOME/
    ...

However, the -l/--loop flag rep loops over stdin in a context like this:

    for i in map(str.rstrip, sys.stdin):
        expressions

Therefore, the above loop can also be written thusly:

    $ ls / | rep -l 'i.upper()'

--pre and --post (-b and -e) options can be used to specify actions to
run before or after the loop. Note that the --pre option is run with
exec instead of eval, and therefore output is never printed, and
statements may be used. This is for things like initializing container
types. --post is automatically printed and statements are not allowed
(unless --quiet is used). --loop is implied if either of these options
are used.

using -s/--split or -F/--field-sep for doing awk things also implies
--loop. The resulting list is named `f` in the execution environment, in
quazi-perl fashion. (oh, and that list is actually a subclass of
collections.UserList that returns an empty string if the index doesn't
exist, so it acts more like awk with empty fields).

Suppressing output and using statements
---------------------------------------
by default, pyfil prints the return value of expressions. Because this
uses eval() internally to get value, statements may not be used. exec()
supports statements, but it does not return the value of expressions
when they are evaluated. When the -q/--quiet flag is used, automatic
printing is suppressed, and expressions are evaluated with exec, so
statements, such as assignments, may be used. Values may still be
printed explicitely.

Home: https://github.com/ninjaaron/pyfil
------------------------------------------------------------------------
'''
import collections
import sys
import json
import os
import re
import ast
import builtins
from functools import update_wrapper
from . import env


class reify(object):
    '"stolen" from Pylons'
    def __init__(self, wrapped):
        self.wrapped = wrapped
        update_wrapper(self, wrapped)

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


class StdIn:
    'class for wrapping sys.stdin'
    def __init__(self):
        self.lines = map(str.rstrip, sys.stdin)

    def __iter__(self):
        return self.lines

    @reify
    def l(self):
        return sys.stdin.read().splitlines()

    def __next__(self):
        return next(self.lines)

    def __getattr__(self, name):
        return getattr(sys.stdin, name)


class SafeList(collections.UserList):
    'class for getting fields from stdin without raising errors'
    def __getitem__(self, index):
        try:
            return self.data[index]
        except IndexError:
            return ''

    def __iter__(self):
        return iter(self.data)


def handle_errors(exception, args):
    if args.raise_errors:
        raise exception
    elif args.silence_errors:
        return
    else:
        print('\x1b[31mError\x1b[0m:', exception)
        return


def run(expressions, args, namespace={}):
    func = exec if args.quiet else eval
    for expr in expressions:
        if args.exception_handler:
            exception, handler = tuple(
                    i.strip() for i in
                    args.exception_handler.split(':', maxsplit=1))
            try:
                value = func(expr, namespace)
            except builtins.__dict__[exception]:
                try:
                    value = func(handler, namespace)
                except Exception as e:
                    handle_errors(e, args)
                    continue
            except Exception as e:
                handle_errors(e, args)
                continue
        else:
            try:
                value = func(expr, namespace)
            except Exception as e:
                handle_errors(e, args)
                continue

        if not args.quiet:
            if args.join is not None and isinstance(value,
                                                    collections.Iterable):
                print(ast.literal_eval("'''" + args.join.replace("'", r"\'") +
                    "'''").join(value))
            elif isinstance(value, collections.Iterator):
                for i in value:
                    print(i)
            else:
                print(value) if value is not None else ...


def main():
    import argparse
    ap = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)

    ap.add_argument('expression', nargs='+', help='expression(s) to be '
                    'executed.')
    ap.add_argument('-l', '--loop', action='store_true',
                    help='for i in sys.stdin: expression')
    ap.add_argument('-q', '--quiet', action='store_true',
                    help='surpress automatic printing; If set, both statments '
                    'and expressions may be used')
    ap.add_argument('-j', '--json', action='store_true',
                    help="load stdin as json into object 'j'; If used with "
                    '--loop, treat each line of stdin as a new object')
    ap.add_argument('-b', '--pre',
                    help='expression to evaluate before the loop')
    ap.add_argument('-e', '--post',
                    help='expression to evaluate after the loop')
    ap.add_argument('-s', '--split', action='store_true',
                    help="split lines from stdin on whitespace into list 'f'. "
                         'implies --loop')
    ap.add_argument('-F', '--field-sep', metavar='PATTERN',
                    help="regex used to split lines from stdin into list 'f'. "
                          "implies -l")
    ap.add_argument('-n', '--join', metavar='STRING',
                    help='join items in iterables with STRING')
    ap.add_argument('-R', '--raise-errors', action='store_true',
                    help='raise errors and in evaluation and stop execution '
                         '(default: print message to stderr and continue)')
    ap.add_argument('-S', '--silence-errors', action='store_true',
                    help='suppress error messages')
    ap.add_argument('-H', '--exception-handler',
                    help='specify exception handler with the format '
                         '`Exeption: alternative expression to eval`')

    a = ap.parse_args()

    func = 'exec' if a.quiet else 'eval'
    expressions = [compile(e, '<string>', func) for e in a.expression]
    user_env = os.environ['HOME'] + '/.config/pyfil-env.py'
    if os.path.exists(user_env):
        namespace = {}
        exec(open(user_env).read(), namespace)
    else:
        namespace = env.__dict__

    namespace.update(stdin=StdIn())

    if a.loop or a.pre or a.post or a.split or a.field_sep:
        if a.pre:
            exec(a.pre, namespace)
        for i in map(str.rstrip, sys.stdin):
            namespace.update(i=i)
            if a.json:
                namespace.update(j=json.loads(i))

            if a.field_sep:
                namespace.update(f=SafeList(re.split(a.field_sep, i)))
            elif a.split:
                namespace.update(f=SafeList(i.split()))

            run(expressions, a, namespace)
        if a.post:
            run((a.post,), a, namespace)

    else:
        if a.json:
            namespace.update(j=json.load(sys.stdin))
        run(expressions, a, namespace)


if __name__ == '__main__':
    main()
