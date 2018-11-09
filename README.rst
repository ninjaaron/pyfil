pyfil
=====
Python one-liners in the spirit of Perl and AWK.

``pyfil`` stands for PYthon FILter. One of the tenants of the `Unix
design`_ is that every program is a filter. It's especially obvious of
programs, like ``grep``, ``sed``, ``sort``, ``tr``, etc.

One notable example is ``awk`` -- a Turing-complete interpreted language
for parsing text. While many AWK scripts are still in use and it's a
capable language in its own right, it has been superseded for scripting
in much of its domain by more general languages like Perl and later
Python and Ruby. However, AWK was designed to be especially useful in
the shell as a filter, and it is still in very common use for that today
(in part because it is on every \*nix system, but also because it's
great at what it does). AWK is able to be any arbitrary text filter that
doesn't come as a coreutil. ``perl -e`` is also quite good in these
applications, and Ruby has made a valiant attempt to be useful in these
circumstances as well.

Python does have a few good one-line uses as well (``python -m
http.server``), some elements of its design make it less suited than the
afore-mentioned languages. ``pyfil`` is one of several attempts to
address this issue. In particular, it takes a lot of queues in the
design of its CLI from AWK and Perl, and aims fundamentally to be a
capable text filter, though it will evaluate any arbitrary Python
expression and print it's output (with modules being imported
implicitly as required).

As a more modern touch, it also has a special emphasis on
interoperability with JSON. If the return value of the evaluated
expression is a container type, python will attempt to serialize it as
JSON before printing, so you can pipe output into other tools that deal
with JSON, store it to a file for later use, or send it over http. This,
combined with the ability to read JSON from stdin (with --json) make
``pyfil`` a good translator between the web, which tends to speak JSON
these days, and the POSIX environment, which tends to think about data
in terms of lines in a file (frequently with multiple fields per line).

pyfil is in pypi (i.e. you can get it easily with pip, if you want)

note:
  pyfil has only been tested with python3, and only has wheels available
  for python3

.. _unix design: https://en.wikipedia.org/wiki/Unix_philosophy

.. contents::

similar projects
----------------
pyfil ain't the first project to try something like this. Here are some
other cracks at this problem:

- oneliner_
- pyp_
- pyle_
- funcpy_
- red_
- pyeval_
- quickpy_

Don't worry. I've stolen some of their best ideas already, and I will go
on stealing as long as it takes!

.. _oneliner: http://python-oneliner.readthedocs.io/en/latest/
.. _pyp: http://code.google.com/p/pyp
.. _pyle: https://github.com/aljungberg/pyle
.. _funcpy: http://www.pixelbeat.org/scripts/funcpy
.. _red: https://bitbucket.org/johannestaas/red
.. _pyeval: https://bitbucket.org/nejucomo/pyeval/wiki/Home
.. _quickpy: https://github.com/slezica/quick-py

usage
-----

.. code::

 pyfil [-h] [-l] [-x] [-q] [-j] [-o] [-b PRE] [-e POST] [-s] [-F PATTERN]
       [-n STRING] [-R] [-S] [-H EXCEPTION_HANDLER]
       expression [expression ...]

positional arguments:
  expression            expression(s) to be executed. If multiple expression
                        arguments are given, and --exec is not used, the value
                        of the previous expression is available as 'x' in the
                        following expression. if --exec is used, all
                        assignment must be explicit.

optional arguments:
  -h, --help            show this help message and exit
  -l, --loop            for n, i in enumerate(stdin): expressions
  -x, --exec            use exec instead of eval. statements are allowed, but
                        automatic printing is lost. doesn't affect --post
  -q, --quiet           suppress automatic printing. doesn't affect --post
  -j, --json            load stdin as json into object 'j'; If used with
                        --loop, treat each line of stdin as a new object
  -J, --real-dict-json  like -j, but creates real dictionaries instead of the
                        wrapper that allows dot syntax.
  -o, --force-oneline-json
                        outside of loops and iterators, objects serialzed to
                        json print with two-space indent. this forces this
                        forces all json objects to print on a single line.
  -b PRE, --pre PRE     statement to evaluate before expression args. multiple
                        statements may be combined with ';'. no automatic
                        printing
  -e POST, --post POST  expression to evaluate after the loop. always handeled
                        by eval, even if --exec, and always prints return
                        value, even if --quiet. implies --loop
  -s, --split           split lines from stdin on whitespace into list 'f'.
                        implies --loop
  -F PATTERN, --field-sep PATTERN
                        regex used to split lines from stdin into list 'f'.
                        implies --loop
  -n STRING, --join STRING
                        join items in iterables with STRING
  -R, --raise-errors    raise errors in evaluation and stop execution
                        (default: print message to stderr and continue)
  -S, --silence-errors  suppress error messages
  -H EXCEPTION_HANDLER, --exception-handler EXCEPTION_HANDLER
                        specify exception handler with the format 'Exception:
                        alternative expression to eval'

available objects
~~~~~~~~~~~~~~~~~
``pyfil`` automatically imports any modules used in expressions.

If you'd like to create any other objects to use in the execution
environment ~/.config/pyfil-env.py and put things in it.

default objects:

- l = []
- d = {}

These are empty containers you might wish to add items to during
iteration, for example.

- x is always the return value of the previous expression unless --exec.

The execution environment also has a special object for stdin,
creatively named ``stdin``. This differs from sys.stdin in that it
strips trailing newlines when you iterate over it, and it has
a property, ``stdin.l``, which returns a list of the lines (without
newlines). If you do want the newlines, access sys.stdin directly.

stdin inherits the rest of its methods from sys.stdin, so you can use
stdin.read() to get a string of all lines, if that's what you need.

Certain other flags may create additional objects in the evaluation
context.

  --loop (or anything that implies --loop) create ``n`` and ``i``.
  --json creates ``j``.
  --split or --field_sep create ``f``
  
Check the flag descriptions for further details.

output
~~~~~~
automatic printing
..................
By default, pyfil prints the return value of expressions. Different
types of objects use different printing conventions.

- ``None`` does not print (as in the REPL)
- strings are sent directly to to ``print()``
- iterators (not other iterables) print each item on a new line.
- other objects are serialized as json. If an object cannot be
  serialized as json, it is sent directly to print().
- all of these are overridden by --join

Iterators will also try to serialize each returned object as json if
they are not strings. json objects will be indented if only one object
is being printed. If --loop is set or several of objects are being
serialzed from an iterator, it will be one object per-line.
--force-oneline-json extends this policy to printing single json objects
as well.

examples:

.. code:: bash

  $ # None gets skipped
  $ pyfil None
  $ # strings and numbers just print
  $ pyfil sys.platfrom
  linux
  $ pyfil math.pi
  3.141592653589793
  $ # objects try to print as json
  $ pyfil sys.path
  [
    "/home/ninjaaron/.local/bin",
    "/usr/lib/python35.zip",
    "/usr/lib/python3.5",
    "/usr/lib/python3.5/plat-linux",
    "/usr/lib/python3.5/lib-dynload",
    "/home/ninjaaron/.local/lib/python3.5/site-packages",
    "/usr/lib/python3.5/site-packages"
  ]
  $ pyfil '{i: n for n, i in enumerate(sys.path)}'
  {
    "/usr/lib/python3.5/plat-linux": 3,
    "/usr/lib/python35.zip": 1,
    "/usr/lib/python3.5": 2,
    "/usr/lib/python3.5/lib-dynload": 4,
    "/usr/lib/python3.5/site-packages": 6,
    "/home/ninjaaron/.local/lib/python3.5/site-packages": 5,
    "/home/ninjaaron/.local/bin": 0
  }
  $ # unless they can't
  $ pyfil '[list, print, re]'
  [<class 'list'>, <built-in function print>, <module 're' from '/usr/lib/python3.5/re.py'>]
  $ # iterators print each item on a new line, applying the same conventions
  $ pyfil 'iter(sys.path)'
  /home/ninjaaron/src/py/pyfil/venv/bin
  /home/ninjaaron/src/py/pyfil
  /usr/lib/python35.zip
  /usr/lib/python3.5
  /usr/lib/python3.5/plat-linux
  /usr/lib/python3.5/lib-dynload
  /home/ninjaaron/src/py/pyfil/venv/lib/python3.5/site-package
  $ pyfil '(i.split('/')[1:] for i in sys.path)'
  ["home", "ninjaaron", "src", "py", "pyfil", "venv", "bin"]
  ["home", "ninjaaron", "src", "py", "pyfil"]
  ["usr", "lib", "python35.zip"]
  ["usr", "lib", "python3.5"]
  ["usr", "lib", "python3.5", "plat-linux"]
  ["usr", "lib", "python3.5", "lib-dynload"]
  ["home", "ninjaaron", "src", "py", "pyfil", "venv", "lib", "python3.5", "site-packages"]

Most JSON is also valid Python, but be aware that you may occasionally
see ``null`` instead of ``None`` along with ``true`` and ``false``
instead of ``True`` and ``False``, and your tuples will look like list.
I guess that's a risk I'm willing to take. (The rational for this is
that pyfil, despite what the name of the ``rep`` command may indicate,
is more about composability in the shell than printing valid Python
literals. JSON is the defacto standard for serialization, or should be,
if only people would stop using XML for that...)

suppressing output and using statements
.......................................
Because these defaults use eval() internally to get value of
expressions, statements may not be used. exec() supports statements, but
it does not return the value of expressions when they are evaluated.
When the -x/--exec flag is used, automatic printing is suppressed, and
expressions are evaluated with exec, so statements, such as assignments,
may be used. Values may still be printed explicitly.

--quite suppresses automatic printing, but eval is still used.

The --post option is immune from --quiet and --exec. It will always be
evaluated with ``eval()``, and it will always try to print. The only
difference is that if --quiet or --exec was used, json will be printed
with indentation unless --force-oneline-json is used.

using files for input and output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``pyfil`` doesn't have any parameters for input and output files. Instead,
use redirection.

.. code:: bash

  pyfil -s 'i.upper()' > output.txt < input.txt

using multiple expression arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``pyfil`` can take as many expressions as desired as arguments. When used
with --exec, this works pretty much as expected, and assignment must be
done manually.

Without --exec, the return value of each expression is assigned to the
variable ``x``, which can be used in the next expression. The final
value of ``x`` is what is ultimately printed, not any intermediate
values.

.. code:: bash

  $ pyfil 'reversed("abcd")' '(i.upper() for i in x)'
  D
  C
  B
  A

looping over stdin
~~~~~~~~~~~~~~~~~~
one can do simple loops with a generator expression. (note that any
expression that evaluates to an iterator will print each item on a new
line unless the ``--join`` option is specified.)

.. code:: bash

    $ ls / | pyfil '(i.upper() for i in stdin)'
    BIN@
    BOOT/
    DEV/
    ETC/
    HOME/
    ...

However, the ``-l``/``--loop`` flag pyfil loops over stdin in a context
like this:

.. code:: python

    for n, i in enumerate(stdin):
        expressions

Therefore, the above loop can also be written thusly:

.. code:: bash

    $ ls / | pyfil -l 'i.upper()'

``--pre`` and ``--post`` (-b and -e) options can be used to specify
actions to run before or after the loop. Note that the --pre option is
run with exec instead of eval, and therefore output is never printed,
and statements may be used. This is for things like initializing
container types. --post is automatically printed and statements are not
allowed (even if --exec is used). --loop is implied if ``--post`` is
used. ``--pre`` can be used without a --loop to do assignments (or
whatever else you may want to do with a statement).

Using ``-s``/``--split`` or ``-F``/``--field-sep`` for doing awk things
also implies --loop. The resulting list is named ``f`` in the execution
environment, in quazi-Perl fashion. (oh, and that list is actually a
subclass of collections.UserList that returns an empty string if the
index doesn't exist, so it acts more like awk with empty fields, rather
than throwing and error and interrupting iteration).

json input
~~~~~~~~~~
``pyfil`` can parse json objects from stdin with the ``-j``/``--json``
flag. They are passed into the environment as the ``j`` object.
combining with the --loop flag will treat stdin as one json object per
line. json objects support dot syntax for attribute access, e.g.
``j.someattr.attr_of_someattr``

formatting output (and 'awk stuff')
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
It's probably obvious that the most powerful way to format strings is
with Python's str.format method and the ``-F`` or ``-s`` options.

.. code:: bash

  $ ls -l /|pyfil -s '"{0}\t{2}\t{8}".format(*f)'
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

  $ ls -l /|pyfil -sn '\t' 'f[0], f[2], f[8]'
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
original utility. This is just to give some ideas of how to use `pyfil`*

replace ``wc -l``:

.. code:: bash

  $ ls / | pyfil 'len(stdin.l)'
  20

replace ``fgrep``:

.. code:: bash

  $ ls / | pyfil '(i for i in stdin if "v" in i)'
  $ ls / | pyfil -l 'i if "v" in i else None'


replace ``grep``:

.. code:: bash

  $ ls / | pyfil 'filter(lambda x: re.search("^m", x), stdin)'
  $ ls / | pyfil -lS 're.search("^m", i).string)'
  $ # using the -S option to suppress a ton of error messages

replace ``sed 's/...``:

.. code:: bash

  $ ls / | pyfil -l 're.sub("^([^aeiou][aeiou][^aeiou]\W)", lambda m: m.group(0).upper(), i)'
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
comfortable doing the traditional way with ``pyfil`` (coreutils are
heavily optimized). Python is interesting for this use-case because it
offers great logic, anonymous functions and all kinds of other goodies
that only full-fledged, modern programming language can offer. Use
coreutiles for the jobs they were designed to excel in. Use ``pyfil`` to
do whatever they can't... and seriously, how will coreutils do this?:

.. code:: bash

  $ wget -qO- http://pypi.python.org/pypi/pyfil/json/ | pyfil -j 'j.urls[0].filename'
  pyfil-0.5-py3-none-any.whl
  $ ls -l | pyfil -qSs \
  "d.update({f[8]: {'permissions': f[0], 'user': f[2], 'group': f[3],
                    'size': int(f[4]), 'timestamp': ' '.join(f[5:8])}})" \
  --post 'd'
.. code:: json

  {
    "README.rst": {
      "group": "users",
      "user": "ninjaaron",
      "permissions": "-rw-r--r--",
      "timestamp": "Sep 6 20:55",
      "size": 18498
    },
    "pyfil/": {
      "group": "users",
      "user": "ninjaaron",
      "permissions": "drwxr-xr-x",
      "timestamp": "Sep 6 20:20",
      "size": 16
    },
    "setup.py": {
      "group": "users",
      "user": "ninjaaron",
      "permissions": "-rw-r--r--",
      "timestamp": "Sep 6 20:30",
      "size": 705
    },
    "LICENSE": {
      "group": "users",
      "user": "ninjaaron",
      "permissions": "-rw-r--r--",
      "timestamp": "Sep 3 13:32",
      "size": 1306
    }
  }

Other things which might be difficult with coreutils:

.. code:: bash

  $ ls / | pyfil -n '  ' 'reversed(stdin.l)'
  var/  usr/  tmp/  sys/  srv/  sbin@  run/  root/  proc/  opt/  ...
  $ # ^^ also, `ls /|pyfil -n '  ' 'stdin.l[::-1]'

error handling
~~~~~~~~~~~~~~
If pyfil encounters an exception while evaluating user input the default
is to print the error message to stderr and continue (if looping over
stdin), as we saw in the section on formatting output. However, errors
can also be silenced entirely with the ``-S``/``--silence-errors``
option. In the below example, the first line produces an error, but we
don't hear about it.

.. code:: bash

  $ ls -l /|pyfil -sS '"{0}\t{2}\t{8}".format(*f)' 
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

  $ ls -l /|pyfil -sR '"{0}\t{2}\t{8}".format(*f)'
  Traceback (most recent call last):
    File "/home/ninjaaron/src/py/pyfil/venv/bin/pyfil", line 9, in <module>
      load_entry_point('pyfil', 'console_scripts', 'pyfil')()
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

  $ ls -l /|pyfil -sH 'IndexError: i' '"{0}\t{2}\t{8}".format(*f)'
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

``ls -l / | pyfil -s '"{0}\t{2}\t{8}".format(*f) if f[2] else i'``

Easy-peasy.
