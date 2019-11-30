from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='clashcli',
    version='0.0.1',
    description='A cli tool for clash or clash RESTful API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/wangl-cc/clashcli',
    author='Long Wang',
    license='GPLv3',
    packages=['clashcli'],
    python_requires='>=3.6',
    entry_points={'console_scripts': ['clashcli=clashcli:main']}
)
