pyfil
=====
This ain't the first project of this kind, and it won't be the last, but
this one is special because it's all mine. ``pyeval`` is a more
mature project of a similar sort. Some might accuse ``pyeval`` of
feature creep, but I would never do that, because I'm totally not
jealous that they did it first. :D

Pretty sure there are other projects like this, too. It's sort of an
obvious thing to try to do: Python one-liners in the spirit of Perl and
AWK.

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

note:
  pyfil has only been tested with python3, and only has wheels available
  for python3

usage
-----

usage: rep [-h] [-l] [-q] [-j] [-b PRE] [-e POST] [-s] [-F PATTERN]
           [-n STRING] [-R] [-S] [-H EXCEPTION_HANDLER]
           expression [expression ...]

positional arguments:
  expression            expression(s) to be executed.

optional arguments:
  -h, --help            show this help message and exit
  -l, --loop            for i in sys.stdin: expression
  -q, --quiet           suppress automatic printing; If set, both statements
                        and expressions may be used
  -j, --json            load stdin as json into object 'j'; If used with
                        --loop, treat each line of stdin as a new object
  -b PRE, --pre PRE     expression to evaluate before the loop
  -e POST, --post POST  expression to evaluate after the loop
  -s, --split           split lines from stdin on whitespace into list 'f'.
                        implies --loop
  -F PATTERN, --field-sep PATTERN
                        regex used to split lines from stdin into list 'f'.
                        implies -l
  -n STRING, --join STRING
                        join items in iterables with STRING
  -R, --raise-errors    raise errors in evaluation and stop execution
                        (default: print message to stderr and continue)
  -S, --silence-errors  suppress error messages
  -H EXCEPTION_HANDLER, --exception-handler EXCEPTION_HANDLER
                        specify exception handler with the format ``Exception:
                        alternative expression to eval``


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

suppressing output and using statements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
by default, pyfil prints the return value of expressions. Because this
uses eval() internally to get value, statements may not be used. exec()
supports statements, but it does not return the value of expressions
when they are evaluated. When the -q/--quiet flag is used, automatic
printing is suppressed, and expressions are evaluated with exec, so
statements, such as assignments, may be used. Values may still be
printed explicitly.

looping over stdin
~~~~~~~~~~~~~~~~~~
one can do simple loops with a generator expression. (note that any
expression that evaluates to an iterator will print each item on a new
line unless the ``--join`` option is specified.)

.. code:: bash

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

.. code:: bash

    $ ls / | rep -l 'i.upper()'

``--pre`` and ``--post`` (-b and -e) options can be used to specify
actions to run before or after the loop. Note that the --pre option is
run with exec instead of eval, and therefore output is never printed,
and statements may be used. This is for things like initializing
container types. --post is automatically printed and statements are not
allowed (unless --quiet is used). --loop is implied if either of these
options are used.

Using ``-s``/``--split`` or ``-F``/``--field-sep`` for doing awk things
also implies --loop. The resulting list is named ``f`` in the execution
environment, in quazi-Perl fashion. (oh, and that list is actually a
subclass of collections.UserList that returns an empty string if the
index doesn't exist, so it acts more like awk with empty fields, rather
than throwing and error and interrupting iteration).

json
~~~~
by popular demand, pyfil can parse json objects from stdin with the
``-j``/``--json`` flag. They are passed into the environment as the
``j`` object.  combining with the --loop flag will treat stdin as one json
object per line.

formatting output (and 'awk stuff')
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
It's probably obvious that the most powerful way to format strings is
with Python's str.format method and the ``-F`` or ``-s`` options.

.. code:: bash

  $ ls -l /|rep -s '"{0}\t{2}\t{8}".format(*f)'
  Error: tuple index out of range
  lrwxrwxrwx	root	bin
  drwxr-xr-x	root	boot/
  drwxr-xr-x	root	dev/
  drwxr-xr-x	root	etc/
  drwxr-xr-x	root	home/
  lrwxrwxrwx	root	lib
  ...

However, you will note that using ``string.format(*f)`` produces an
error and does not print anything to stdout (error message is sent to
stderr; see error handling for more options) for lines without enough
fields, which may not be the desired behavior when dealing with lines
containing arbitrary numbers of fields.

For simpler cases, you may wish to use the ``-n``/``--join`` option,
which will join any iterables with the specified string before printing,
and, in the case of the ``f`` list, will replace any none-existent
fields with an empty string.

.. code:: bash

  $ ls -l /|rep -sn '\t' 'f[0], f[2], f[8]'
  total		
  lrwxrwxrwx	root	bin
  drwxr-xr-x	root	boot/
  drwxr-xr-x	root	dev/
  drwxr-xr-x	root	etc/
  drwxr-xr-x	root	home/
  lrwxrwxrwx	root	lib

In this case, the first line of ``ls -l /`` provides values for all
available fields.

Technical note:
    The separator specified with the ``--join`` option is implemented
    internally as ``ast.literal_eval("'''"+STRING.replace("'",
    r"\'")+"'''")``. If one works hard at it, it is possible to pass
    values which will cause pyfil to crash; i.e. patterns ending with a
    backslash. Keep in mind rules about escape sequences in the shell and
    in python if you absolutely must have a pattern that terminates with
    a backslash. (The reason it is implemented this way is to allow the
    use of escape sequences that are meaningful to the python, but not
    the shell, such as \\n, \\t, \\x, \\u, etc.)

examples
~~~~~~~~

*I realize that it's much better to do most of these things with the
original utility. This is just to give some ideas of how to use `rep`*

replace ``wc -l``:

.. code:: bash

  $ ls / | rep 'len(stdin.l)'
  20

replace ``fgrep``:

.. code:: bash

  $ ls / | rep '(i for i in stdin if "v" in i)'
  $ ls / | rep -l 'i if "v" in i else None'


replace ``grep``:

.. code:: bash

  $ ls / | rep '(i for i in stdin if re.search("^m", i))'
  $ ls / | rep 'filter(lambda x: re.search("^m", x), stdin)'

replace ``sed 's/...``:

.. code:: bash

  $ ls / | rep -l 're.sub("^([^aeiou][aeiou][^aeiou]\W)", lambda m: m.group(0).upper(), i)'
  BIN@
  boot/
  data/
  DEV/
  etc/
  ...

This example illustrates that, while you might normally prefer ``sed``
for replacement tasks, the ability to define a replacement function with
``re.sub`` does offer some interesting possibilities. Indeed, someone
familiar with coreutils should never prefer to do something they already
comfortable doing the traditional way with ``rep`` (coreutils are
heavily optimized). Python is interesting for this use-case because it
offers great logic, anonymous functions and all kinds of other goodies
that only full-fledged, modern programming language can offer. Use
coreutiles for the jobs they were designed to excel in. Use ``rep`` to
do whatever they can't... and seriously, how will coreutils do this?:

.. code:: bash

  $ wget -qO- http://pypi.python.org/pypi/pyfil/json/ | rep -j 'j["urls"][0]["filename"]'
  pyfil-0.5-py3-none-any.whl


Other things which might be difficult with coreutils:

.. code:: bash

  $ ls / | rep -n '  ' 'reversed(stdin.l)'
  var/  usr/  tmp/  sys/  srv/  sbin@  run/  root/  proc/  opt/  ...
  $ # ^^ also, `ls /|rep -n '  ' 'stdin.l[::-1]'
  $
  $ 

error handling
~~~~~~~~~~~~~~
If pyfil encounters an exception while evaluating user input the default
is to print the error message to stderr and continue (if looping over
stdin), as we saw in the section on formatting output. However, errors
can also be silenced entirely with the ``-S``/``--silence-errors``
option. In the below example, the first line produces an error, but we
don't hear about it.

.. code:: bash

  $ ls -l /|rep -sS '"{0}\t{2}\t{8}".format(*f)' 
  lrwxrwxrwx	root	bin
  drwxr-xr-x	root	boot/
  drwxr-xr-x	root	dev/
  drwxr-xr-x	root	etc/
  drwxr-xr-x	root	home/
  lrwxrwxrwx	root	lib
  ...

Alternatively, errors may be raised when encountered, which will stop
execution and give a (fairly useless, in this case) traceback. This is
done with the ``-R``/``--raise-errors`` flag.

.. code:: bash

  $ ls -l /|rep -sR '"{0}\t{2}\t{8}".format(*f)'
  Traceback (most recent call last):
    File "/home/ninjaaron/src/py/pyfil/venv/bin/rep", line 9, in <module>
      load_entry_point('pyfil', 'console_scripts', 'rep')()
    File "/home/ninjaaron/src/py/pyfil/pyfil/pyfil.py", line 242, in main
      run(expressions, a, namespace)
    File "/home/ninjaaron/src/py/pyfil/pyfil/pyfil.py", line 164, in run
      handle_errors(e, args)
    File "/home/ninjaaron/src/py/pyfil/pyfil/pyfil.py", line 134, in handle_errors
      raise exception
    File "/home/ninjaaron/src/py/pyfil/pyfil/pyfil.py", line 162, in run
      value = func(expr, namespace)
    File "<string>", line 1, in <module>
  IndexError: tuple index out of range

In addition to these two handlers, it is possible to specify a
rudimentary custom handler with the ``-H``/``--exception-handler``
flags. The syntax is ``-H 'Exception: expression'``, where ``Exception``
can be any builtin exception class (including Exception, to catch all
errors), and ``expression`` is the alternative expression to evaluate
(and print, if not --quiet).

.. code:: bash

  $ ls -l /|rep -sH 'IndexError: i' '"{0}\t{2}\t{8}".format(*f)'
  total 32
  lrwxrwxrwx	root	bin
  drwxr-xr-x	root	boot/
  drwxr-xr-x	root	dev/
  drwxr-xr-x	root	etc/
  drwxr-xr-x	root	home/
  lrwxrwxrwx	root	lib
  ...

In this case, we've chosen to print line without any additional
formatting. If other errors are encountered, it will fall back to other
handlers (``-S``, ``-R``, or the default). For more sophisticated error
handling... Write a real Python script, where you can handle to your
heart's content.

Also note that this case is possible to handle with a test instead of an
exception handler because ``f`` is a special list that will return an
empty string instead of throw an index error if the index is out of
range:

``ls -l / | rep -s '"{0}\t{2}\t{8}".format(*f) if f[2] else i'``

Easy-peasy.
