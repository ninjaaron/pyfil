pyfil
=====
This ain't the first project of this kind, and it won't be the last, but
this one is special because it's all mine. ``pyeval`` is a more
mature project of a similar sort. Some might accuse ``pyeval`` of
feature creep, but I would never do that, because I'm totally not
jealous that they did it first. :D

Pretty sure there are other projects like this, too. It's sort of an
obvious thing to try to do.

``pyfil`` gives you the ``rep`` command. This is because when I
initially posted it in #python IRC channel, user [Tritium] (that ray of
sunshine) said I had recreated the REP of the python REPL (read evaluate
print loop). That is more or less the case. ``rep`` reads python
expressions at the command line, evaluates them and prints them to
stdout. It might be interesting as a quick calculator or to test
something, like the Python REPL, but it also has some special flags for
iterating on stdin and parsing JSON, which make it useful as a filter
for shell one-liners or scripts (like Perl).

pyfil is in pypi (i.e. you can get it easily with pip, if you want)

usage
-----

available objects
~~~~~~~~~~~~~~~~~
Automatically imports (unless overridden in ~/.config/pyfil-env.py):
    ``sys``, ``os``, ``re``, ``math``, ``pprint from pprint``, ``timeit
    from timeit`` and ``strftime from time``.

If you'd like to specify a custom execution environment for rep, create
~/.config/pyfil-env.py and put things in it.

The execution environment also has a special object for stdin,
creatively named ``stdin``. This differs from sys.stdin in that it
rstrips (aka chomps) all the lines when you iterate over it, and it has
a property, ``stdin.l``, which returns a list of the (rstripped) lines.
pyfil is quite bullish about using rstrip because python's print
function will supply an additional newline, and if you just want the
value of the text in the line, you almost never want the newline
character. If you do want the newlines, access sys.stdin directly.

stdin inherits the rest of its methods from sys.stdin, so you can use
stdin.read() to get a string of all lines, if that's what you need.

looping over stdin
~~~~~~~~~~~~~~~~~~
one can do simple loops with a generator expression. (note that any
expression that evaluates to an iterator will print each item on a new
line)

.. code::

    $ ls / | rep '(i.upper() for i in stdin)'
    BIN@
    BOOT/
    DEV/
    ETC/
    HOME/
    ...

However, the ``-l``/``--loop`` flag rep loops over stdin in a context
like this:

.. code:: python

    for i in map(str.rstrip, sys.stdin):
        expressions

Therefore, the above loop can also be written thusly:

.. code::

    $ ls / | rep -l 'i.upper()'

``--pre`` and ``--post`` (-b and -e) options can be used to specify
actions to run after the loop. Note that the --pre option is run with
exec instead of eval, and therefore output is never printed, and
statements may be used. This is for things like initializing container
types. --post is automatically printed and statements are not allowed
(unless --quiet is used). --loop is implied if either of these options
are used.

Using ``-s``/``--split`` or ``-F``/``--field-sep`` for doing awk things
also implies --loop. The resulting list is named ``f`` in the execution
environment, in quazi-Perl fashion.

Suppressing output and using statements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
by default, pyfil prints the return value of expressions. Because this
uses eval() internally to get value, statements may not be used. exec()
supports statements, but it does not return the value of expressions
when they are evaluated. When the -q/--quiet flag is used, automatic
printing is suppressed, and expressions are evaluated with exec, so
statements, such as assignments, may be used. Values may still be
printed explicitely.

json
~~~~
by popular demand, pyfil can parse json objects from stdin with the
-j/--json flag. They are passed into the environment as the ``j``
object.  combining with the -l flag will treat stdin as one json object
per line.
