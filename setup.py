from setuptools import setup

setup(
    name='pyfil',
    version='0.5',
    author='Aaron Christianson',
    license='BSD',
    author_email='ninjaaron@gmail.com',
    url='https://github.com/ninjaaron/pyfil',
    description='print the return value of python expression -- also in loops',
    long_description=open('README.rst').read(),
    keywords='evaluate',
    packages=['pyfil'],
    entry_points={'console_scripts': ['rep=pyfil.pyfil:main']},
)
