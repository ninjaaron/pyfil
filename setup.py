from setuptools import setup
try:
    from urllib import request
except ImportError:
    import urllib2 as request

fastep = request.urlopen('https://raw.githubusercontent.com/ninjaaron/fast-entry_points/master/fastentrypoints.py')
namespace = {}
exec(fastep.read(), namespace)

setup(
    name='pyfil',
    version='0.17',
    author='Aaron Christianson',
    license='BSD',
    author_email='ninjaaron@gmail.com',
    url='https://github.com/ninjaaron/pyfil',
    description='Python one-liners in the shell in the spirit of Perl and AWK',
    long_description=open('README.rst').read(),
    keywords='evaluate',
    packages=['pyfil'],
    entry_points={'console_scripts': ['rep=pyfil.pyfil:main']},
)
