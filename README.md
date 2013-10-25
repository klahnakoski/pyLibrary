pyLibrary
=========


A library of general functions

  * **basic.py** - Simple functions with no home

  * **cnv.py** - Convert between types, methods are in the form of ```<from_type> "2" <to_type>``` so
I am better able to remember them

  * **db.py** - Simplify the MySQL client API, specifically to parametrize SQL easier

  * **elasticsearch.py** - Interact with Elasticsearch

  * **emailer.py** - Simple email

  * **files.py** - Default utf8, and because I can not remember the builtin file functions

  * **logs.py** - Exception chaining, threaded and structured logging

  * **maths.py** - Extra math functions, with proper mapping of missing values

  * **multiset.py** - who doesn't need a multiset?

  * **multithread.py** - optimized for symmetric multi-threading (not real threads, for course)

  * **multiprocess.py** - optimized for symmetric multi-processing (incomplete)

  * **query.py** - Named methods for very common set/list comprehensions

  * **queries/windows.py** - Window functions for list comprehensions

  * **randoms.py** - Because random should be easy to remember

  * **startup.py** - because application parameters should all be in one place and NOT HIDING IN ENVIRONMENT VARIABLES!!

  * **stats.py** - Statistical functions with missing value handling

  * **strings.py** - String functions:  Mostly giving familiar names to Python equivalent.

  * **struct.py** - Basis for proper missing-value (Null) handling on list comprehensions

  * **threads.py** - Because, somehow, the standard lib go it wrong

  * **timer.py** - The way timers are meant to be (using the ```with``` clause)
  
  



Windows 7 Install Instructions 
------------------------------

Python was really made for Linux, and installation will be easier there.  Technically, Python works on Windows too, but
there are a few gotchas you can avoid by following these instructions.

  * Download Python 2.7 (32bit ONLY!!! Many native libs are 32 bit)
  * Install Python at c:\Python27 (The space in the "Program Files" may screw up installs of native libs)
  * Add to you path: ```c:\Python27;c:\Python27\scripts;```
  * Download ```http://python-distribute.org/distribute_setup.py```
 
        CALL python distribute_setup.py
        CALL easy_install pip
        CALL easy_install virtualenv

  * Many "Python Powered" native installs require a pointer to the python installation, but they have no idea where to
  look in 64bit windows.  You must alter the registry ([http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows](http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows)):
  
        SET HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Python\PythonCore\2.7\InstallPath = "C:\Python27"

  * Download from Github:

     	git clone https://github.com/klahnakoski/pyLibrary.git

  * Download requirements:

		pip install -r requirements.txt

Optional
--------

pyLibrary does not use these, but maybe you will find the useful:

  * Install MySqldb from [http://sourceforge.net/projects/mysql-python/files/mysql-python/](http://sourceforge.net/projects/mysql-python/files/mysql-python/)
  * Install ujson from [http://www.lfd.uci.edu/~gohlke/pythonlibs/#ujson](http://www.lfd.uci.edu/~gohlke/pythonlibs/#ujson)