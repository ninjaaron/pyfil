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
run after the loop. Note that the --pre option is run with exec instead
of eval, and therefore output is never printed, and statements may be
used. This is for things like initializing container types. --pre is
automatically printed and statements are not allowed (unless --quiet is
used).

Suppressing output and using statements
---------------------------------------
by default, pyfil prints the return value of expressions. Because this
uses eval() internally to get value, statements may not be used. exec()
supports statements, but it does not return the value of expressions
when they are evaluated. When the -q/--quiet flag is used, automatic
printing is suppressed, and expressions are evaluated with exec, so
statements, such as assignments, may be used. Values may still be
printed explicitely.

json
----
by popular demand, pyfil can parse json objects from stdin with the
-j/--json flag. They are passed into the environment as the `j` object.
combining with the -l flag will treat stdin as one json object per line.

Home: https://github.com/ninjaaron/pyfil
------------------------------------------------------------------------
'''
import collections
import sys
import json
import os
from . import env
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


class StdIn:
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


def run(expressions, quiet=False, namespace={}):
    func = exec if quiet else eval
    for expr in expressions:
        value = func(expr, namespace)
        if not quiet:
            if isinstance(value, collections.Iterator):
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

    if a.loop:
        if a.pre:
            exec(a.pre, namespace)
        for i in map(str.rstrip, sys.stdin):
            namespace.update(i=i)
            if a.json:
                namespace.update(j=json.loads(i))
            run(expressions, a.quiet, namespace)
        if a.post:
            run((a.post,), a.quiet, namespace)

    else:
        if a.json:
            namespace.update(j=json.load(sys.stdin))
        run(expressions, a.quiet, namespace)


if __name__ == '__main__':
    main()
