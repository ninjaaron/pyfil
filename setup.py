from setuptools import setup

setup(
    name='pyrep',
    version='0.0',
    author='Aaron Christianson',
    license='BSD',
    author_email='ninjaaron@gmail.com',
    # url='https://github.com/ninjaaron/???',
    description='print the return value of python expression -- also in loops',
    long_description=open('README.rst').read(),
    keywords='evaluate',
    packages=['pyrep'],
    entry_points={'console_scripts': ['rep=pyrep.pyrep:main']},
)
