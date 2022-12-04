# encoding: utf-8
# THIS FILE IS AUTOGENERATED!
from __future__ import unicode_literals
from setuptools import setup
setup(
    author='Kyle Lahnakoski',
    author_email='kyle@lahnakoski.com',
    classifiers=["Development Status :: 4 - Beta","Topic :: Software Development :: Libraries","Topic :: Software Development :: Libraries :: Python Modules","Programming Language :: Python :: 3.7","Programming Language :: Python :: 3.8","Programming Language :: Python :: 3.9","License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"],
    description='Library of Wonderful Things',
    extras_require={"tests":["numpy","fastparquet"]},
    include_package_data=False,
    install_requires=["requests"],
    license='MPL 2.0',
    long_description='# pyLibrary\n\nA library of wonderful Python things!\n\n## Motivation\n\nThis library is born from my version of the `utils` library every project has.\nOnly, instead of being utilities that are specific to the task, these utilities\nare for multiple projects: They assume logs should be structured,\nall data should be JSONizable, and OO is preferred, and more.\n\n### Python is a Little Crufty ###\n\nPython is awesome now, but it was originally a procedural language invented\nbefore pure functional semantics, before OO, and even before the\ndiscovery of vowels.  As a consequence there are many procedures that alter\ntheir own parameters, or have disemvoweled names.  This library puts a facade\nover these relics of the past and uses convention to name methods.\n\n## Installing pyLibrary\n\nPython packages are easy to install, assuming you have Python (see below).\n\n    pip install pyLibrary\n\n## Installing for Development\n\n  * Download from Github:\n\n        git clone https://github.com/klahnakoski/pyLibrary.git\n\n  * Install requirements:\n\n        python setup.py develop\n\n\nWindows 7 Install Instructions for Python\n-----------------------------------------\n\nUpdated November 2014, for Python 2.7.8\n\nPython was really made for Linux, and installation will be easier there.\nTechnically, Python works on Windows too, but there are a few gotchas you can\navoid by following these instructions.\n\n  * Download Python 2.7\n    * 32bit ONLY!!! Many native libs are 32 bit\n    * Varsion 2.7.8 or higher (includes pip, so install is easier)\n  * Install Python at ```c:\\Python27``` (The space in the "Program Files" may screw up installs of native libs)\n  * Add to you path: ```c:\\Python27;c:\\Python27\\scripts;```\n  * Download ```https://bootstrap.pypa.io/get-pip.py```\n\n        CALL python get-pip.py\n        CALL pip install virtualenv\n\n  * Many "Python Powered" native installs require a pointer to the python installation, but they have no idea where to\n  look in 64bit windows.  You must alter the registry ([http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows](http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows)):\n\n        SET HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Python\\PythonCore\\2.7\\InstallPath = "C:\\Python27"\n\n###Using virtualenv\n\n```virtualenv``` allows you to have multiple python projects on the same\nmachine, even if they use different versions of the same libraries.\n```virtualenv``` does this by making a copy of the main python directory and\nusing it to hold the specific versions required.\n\n* New environment: ```virtualenv <name_of_dir>```\n* Activate environment: ```<name_of_dir>\\scripts\\activate```\n* Exit environment: ```deactivate```\n\nIf you have more than one project on your dev box I suggest you do all your\nwork inside a virtual environment.\n\n### PyPy and Virtual Environments\n\n```virtualenv``` can be used with PyPy, but it is a bit more involved.  The\npaths must be explict, and some copying is required.\n\n#### New environment:\nThe first call to virtualenv will make the directory, to which you copy the\nPyPy core libraries, and the second call finishes the install.\n\n    c:\\PyPy27\\bin\\virtualenv <name_of_dir>\n    copy c:\\PyPy27\\bin\\lib_pypy <name_of_dir>\n    copy c:\\PyPy27\\bin\\lib_python <name_of_dir>\n    c:\\PyPy27\\bin\\virtualenv <name_of_dir>\n\n#### Activate environment:\nWith CPython ```virtualenv``` places it\'s executables in ```Scripts```.  The\nPyPy version uses ```bin```\n\n    <name_of_dir>\\bin\\activate\n\n#### Using PIP in PyPy:\n\nPyPy does not share any libraries with CPython.  You must install the PyPy libraries using \n\n\tC:\\pypy\\bin\\pip.exe\n\nThe `pip` found in your `%PATH%` probably points to `C:\\python27\\Scripts\\pip.exe`.\n\n#### Using PIP in PyPy virtualenv:\n\nDo **NOT** use the ```<name_of_dir>\\Scripts``` directory: It installs to your\nmain PyPy installation.  Pip install is done using the `bin` directory:\n\n    <name_of_dir>\\bin\\pip.exe\n\n#### Exit environment:\nDeactivation is like normal\n\n    deactivate\n\n### CPython Binaries and Virtual Environments\n\nIf you plan to use any binary packages, ```virtualenv``` will not work\ndirectly.  Instead, install the binary (32 bit only!!) to the main python\ninstallation.  Then copy any newly installed files/directories from\n```C:\\Python27\\Lib\\site-packages``` to ```<name_of_dir>\\Lib\\site-packages```.\n\n### Binaries and PyPy\n\nThis strategy for installing binaries into Virtual Environments is almost\nidentical to installing binaries into your PyPy environment: Install Numpy\nand Scipy to your CPython installation using a windows installer (which has\npre-compiled binaries), and then copy the ```C:\\Python27\\Lib\\site-packages\\<package>```\nto ```c:\\PyPy\\site-packages\\```; note lack of ```Lib``` subdirectory.\n\n',
    long_description_content_type='text/markdown',
    name='pyLibrary',
    packages=["pyLibrary/aws","pyLibrary/env","pyLibrary"],
    url='https://github.com/klahnakoski/pyLibrary',
    version='3.264.22338'
)