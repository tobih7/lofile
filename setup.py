# lool #

import setuptools


# VERSION
with open('src/lofile/core/__init__.py') as file:
    for line in file.readlines():
        if '__version__' in line:
            __version__: str
            exec(line)


# SETUP
setuptools.setup(

    name = 'lofile-lool',
    version = __version__,
    author = 'lool',
    author_email = 'txhx@gmail.com',
    description = 'The lofile package!',
    url = 'https://github.com/user3838',

    package_dir = {'': 'src'},
    packages = setuptools.find_packages('src'),
    python_requires = '>= 3.8',
    install_requires = ['pycryptodome'],

    entry_points = {
        'console_scripts': [
            'lofile = lofile.cli:main'
        ]
    }

)
