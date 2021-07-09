# lool #

from setuptools import setup, find_packages
from subprocess import call


# VERSION
with open('src/lofile/core/__init__.py') as file:
    for line in file.readlines():
        if '__version__' in line:
            __version__: str
            exec(line.strip())
            break


# SETUP
setup(

    name = 'lofile',
    version = __version__,
    author = 'lool',
    author_email = 'txhx38@gmail.com',
    description = 'The lofile package!',
    url = 'https://github.com/txhx38/lofile',

    package_dir = {'': 'src'},
    packages = find_packages('src'),
    python_requires = '>= 3.8',
    install_requires = ['pycryptodome'],

    entry_points = {
        'console_scripts': [
            'lofile = lofile.cli:main'
        ]
    }

)
