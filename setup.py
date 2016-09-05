from setuptools import setup

setup(
    name='pyfil',
    version='0.7',
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
