#!/usr/bin/env python3
'''
Evaluate python expressions. Print the return value. If the return value
is an iterator, print each item on its own line.

rep automatically imports any modules used in expressions.

If you'd like to create any other objects to use in the execution
environment ~/.config/pyfil-env.py and put things in it.

The execution environment also has a special object for stdin,
creatively named "stdin". This differs from sys.stdin in that it
rstrips (aka chomps) all the lines when you iterate over it, and it has
a property, stdin.l, which returns a list of the (rstripped) lines.

Home: https://github.com/ninjaaron/pyfil
'''
import collections
import sys
import json
import os
import re
import ast
from functools import update_wrapper


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


class NameSpace(dict):
    'namespace that imports modules lazily.'
    def __missing__(self, name):
        return __import__(name)


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
        pass
    else:
        print('\x1b[31mError\x1b[0m:', exception, file=sys.stderr)


def print_obj(obj):
    if isinstance(obj, str):
        print(obj)
    else:
        try:
            print(json.dumps(obj, ensure_ascii=False))
        except TypeError:
            print(obj)


def run(expressions, args, namespace={}):
    func = exec if args.quiet else eval
    for expr in expressions:
        if args.exception_handler:
            exception, handler = tuple(
                    i.strip() for i in
                    args.exception_handler.split(':', maxsplit=1))
            try:
                value = func(expr, namespace)
            except __builtins__[exception]:
                try:
                    value = func(handler, namespace)
                except Exception as e:
                    value = handle_errors(e, args)
                    continue
            except Exception as e:
                value = handle_errors(e, args)
                continue
        else:
            try:
                value = func(expr, namespace)
            except Exception as e:
                value = handle_errors(e, args)
                continue

        if not args.quiet:
            namespace.update(x=value)

    if not args.quiet:
        if args.join is not None and isinstance(value, collections.Iterable):
            print(ast.literal_eval("'''" + args.join.replace("'", r"\'") +
                "'''").join(value))
        elif value is None:
            pass
        elif isinstance(value, collections.Iterator):
            for i in value:
                print_obj(i)
        else:
            print_obj(value)


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
                    help='suppress automatic printing; If set, both statements'
                    ' and expressions may be used')
    ap.add_argument('-j', '--json', action='store_true',
                    help="load stdin as json into object 'j'; If used with "
                    '--loop, treat each line of stdin as a new object')
    ap.add_argument('-b', '--pre',
                    help='statement to evaluate before expressions')
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
                    help='raise errors in evaluation and stop execution '
                         '(default: print message to stderr and continue)')
    ap.add_argument('-S', '--silence-errors', action='store_true',
                    help='suppress error messages')
    ap.add_argument('-H', '--exception-handler',
                    help='specify exception handler with the format '
                         '`Exception: alternative expression to eval`')

    a = ap.parse_args()

    func = 'exec' if a.quiet else 'eval'
    expressions = [compile(e, '<string>', func) for e in a.expression]
    user_env = os.environ['HOME'] + '/.config/pyfil-env.py'
    namespace = NameSpace()
    namespace.update(__builtins__)
    if os.path.exists(user_env):
        exec(open(user_env).read(), namespace)

    namespace.update(stdin=StdIn())

    if a.loop or a.post or a.split or a.field_sep:
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
        if a.pre:
            exec(a.pre, namespace)
        if a.json:
            namespace.update(j=json.load(sys.stdin))
        run(expressions, a, namespace)


if __name__ == '__main__':
    main()
