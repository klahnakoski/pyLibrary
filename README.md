pyLibrary
=========

A library of wonderful things!

Motivation
----------

### Python is a Little Crufty ###

Python is awesome now, but it was originally a procedural language invented
before functional semantics, before OO, and even before the
discovery of vowels.  As a consequence there are many procedures that alter
their own parameters, or have disemvoweled names.  This library puts a facade
over these relics of the past and uses convention to name methods.


### Advanced List Comprehensions are Awesome ###

My career has been permeated with the need to write [ETL scripts](http://en.wikipedia.org/wiki/Extract,_transform,_load).
I have preferred SQL for it's succinctness when dealing with data
transformations, and it makes Python's list comprehensions look limited in
comparison.  I have added a few more relational operators, and provided
procedures to handle common complex list comprehensions.


### Nones are Important ###

ETL inherently deals with diverse data and missing data.  This leaves many
opportunities for None to take the place of that missing data.

Heavy use of list comprehensions requires a significantly different strategy when
dealing with Nulls/Nones.  The Pythonic strategy of raising exceptions on
invalid access is unacceptable inside the context of list operations because we
want to process all good data and not exit early.  Furthermore, even the data
with Nones can go through partial processing.

A significant portion of this library implements familiar set/list operations
while dealing with Nones gracefully.  To do this, None is interpreted as
*not-applicable* rather than *unknown/missing*.  The former allows operations
to assume the None can be ignored in the context of the operation, and this
assumption turns out to be mostly correct in the context of ETL.  The latter
interpretation appears more in statistics.   A good example is ```util.collections.AND```:

    AND(True, None, True) == True  # Assuming None means "not applicable"
    AND(True, None, True) == None  # Assuming None means "unknown"

### JSON is Everywhere ###

This library is also designed to query into hierarchical data, like JSON.
Hierarchical queries are made easy by manipulating references to paths into the
JSON trees, and further allowing set comprehensions to use those paths to
deconstruct, or reconstruct trees succinctly.  The dot "```.```" operator is
used to specify paths, and is so prevalent that the literal dot must be escaped
(like so: "```\.```").  JSON, and the paths into it, are an excellent source
of Nones.

### Structured Logging integrated with Chained Exceptions is Good ###

Exception handling and logging are undeniably linked.  There are many instances
where exceptions are raised and must be logged, except when they are
appropriately handled.  The greatness of exception handling semantics comes from
decoupling the cause from the solution, but this is at odds with clean logging -
which couples raising and handling to make appropriate decisions about what to
ultimately emit to the log.  For this reason, the logging module is responsible
for collecting the trace and context, raising the exception, and then deducing
if there is something that will handle it (so it can be ignored), or if it
really must be logged.

This library also expects all log messages and exception messages to have named
parameters so they can be stored in easy-to-digest JSON, which can be processed
by downstream tools.


Windows 7 Install Instructions for Python
-----------------------------------------

Python was really made for Linux, and installation will be easier there.
Technically, Python works on Windows too, but there are a few gotchas you can
avoid by following these instructions.

  * Download Python 2.7 (32bit ONLY!!! Many native libs are 32 bit)
  * Install Python at ```c:\Python27``` (The space in the "Program Files" may screw up installs of native libs)
  * Add to you path: ```c:\Python27;c:\Python27\scripts;```
  * Download ```http://python-distribute.org/distribute_setup.py```

        CALL python distribute_setup.py
        CALL easy_install pip
        CALL easy_install virtualenv

  * Many "Python Powered" native installs require a pointer to the python installation, but they have no idea where to
  look in 64bit windows.  You must alter the registry ([http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows](http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows)):

        SET HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Python\PythonCore\2.7\InstallPath = "C:\Python27"

###Using virtualenv

```virtualenv``` allows you to have multiple python projects on the same
machine, even if they use different versions of the same libraries.
```virtualenv``` does this by making a copy of the main python directory and
using it to hold the specific versions required.

* New environment: ```virtualenv <name_of_dir>```
* Activate environment: ```<name_of_dir>\scripts\activate```
* Exit environment: ```deactivate```

If you have more than one project on your dev box I suggest you do all your
work inside a virtual environment.

### PyPy and Virtual Environments

```virtualenv``` can be used with PyPy, but it is a bit more involved.  The
paths must be explict, and some copying is required.

#### New environment:
The first call to virtualenv will make the directory, to which you copy the
PyPy core libraries, and the second call finishes the install.

    c:\PyPy27\bin\virtualenv <name_of_dir>
    copy c:\PyPy27\bin\lib_pypy <name_of_dir>
    copy c:\PyPy27\bin\lib_python <name_of_dir>
    c:\PyPy27\bin\virtualenv <name_of_dir>

#### Activate environment:
With CPython ```virtualenv``` puts it's executables in ```Scripts```.  The
PyPy version uses ```bin```

    <name_of_dir>\bin\activate

#### Using PIP in PyPy virtualenv:
Do **NOT** use the ```<name_of_dir>\Scripts``` directory: It installs to your
main PyPy installation.  Pip install is done using the ``bin`` directory:

    <name_of_dir>\bin\pip.exe

#### Exit environment:
Deactivation is like normal

    deactivate

### Binaries and Virtual Environments

If you plan to use any binary packages, ```virtualenv``` will not work
directly.  Instead, install the binary (32 bit only!!) to the main python
installation.  Then copy any newly installed files/directories from
```C:\Python27\Lib\site-packages``` to ```<name_of_dir>\Lib\site-packages```


Installing pyLibrary
--------------------

Once Python is installed, other Python packages are are much easier.

  * Install from PyPi:

        pip install pyLibrary

Installing for Development
--------------------------

  * Download from Github:

        git clone https://github.com/klahnakoski/pyLibrary.git

  * Install requirements:

        python setup.py develop

