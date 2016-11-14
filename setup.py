from setuptools import setup
import fastentrypoints

setup(
    name='pyfil',
    version='1.3',
    author='Aaron Christianson',
    license='BSD',
    author_email='ninjaaron@gmail.com',
    url='https://github.com/ninjaaron/pyfil',
    description='Python one-liners in the shell in the spirit of Perl and AWK',
    long_description=open('README.rst').read(),
    keywords='evaluate',
    py_modules=['pyfil'],
    entry_points={'console_scripts': ['rep=pyfil:main', 'pyfil=pyfil:main']},
    classifiers=['Programming Language :: Python :: 3'],
)
