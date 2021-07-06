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
    install_requires = ['pycryptodome']
)



# -----==========-----
#      BUILD .EXE
# -----==========-----
from distutils import sysconfig
from distutils.ccompiler import new_compiler
PyExecCSource = '''
#define Py_LIMITED_API 1
#include <Python.h>
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>

int wmain()
{
    wchar_t **argv = _alloca(2 * sizeof(wchar_t *));
    argv[0] = "-m";
    argv[1] = "lofile";
    return Py_Main(2, argv);
}
'''

