# lool #

import sys, os
from setuptools import setup, find_packages

sys.path.insert(0, os.getcwd() + '\\src')
from lofile import __doc__, __version__

# SETUP
setup(

    name = 'lofile',
    version = __version__,
    author = 'lool',
    author_email = 'txhx38@gmail.com',
    description = __doc__,
    url = 'https://github.com/txhx38/lofile',

    package_dir = {'': 'src'},
    packages = find_packages('src'),
    python_requires = '>= 3.8',
    install_requires = ['pycryptodome', 'loolclitools'],

    entry_points = {
        'console_scripts': [
            'lofile = lofile.cli:main'
        ]
    }

)
