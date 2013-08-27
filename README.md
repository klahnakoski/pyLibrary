pyLibrary
=========


A library of general functions

  * **basic.py** - Simple functions with no home

  * **cnv.py** - Convert between types, methods are in the form of {from_type} "2" {to_type} so
I am better able to remember them

  * **db.py** - Simplify the MySQL client API, specifically to parametrize SQL easier

  * **emailer.py** - Simple email

  * **map.py** - Allow dictionary access vis dot operator

  * **maths.py** - Extra math functions

  * **query.py** - Named methods for very common list comprehensions

  * **stats.py** - Statistical functions

  * **strings.py** - String functions:  Mostly giving names I am familiar with to Python equivalent.
  
  
Windows 7 Install Instructions 
==============================

April 2013:

  * Install Python 2.7 (32bit ONLY!!! Many native libs are 32 bit)
  * Install Python at c:\Python27 (The space on "program files" may screw up installs of nativ libs)
  * Add to you path: ```c:\Python27;c:\Python27\scripts;```
  * Download ```http://python-distribute.org/distribute_setup.py```
 
        CALL python distribute_setup.py
        CALL easy_install pip
        CALL easy_install virtualenv

  * Many "Python Powered" native installs require a pointer to the python installation, but they have no idea where to look in 64bit windows.  You must alter the registry([http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows](http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows)):
  
        SET HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Python\PythonCore\2.7\InstallPath = "C:\Python27"

  * Install MySqldb from [http://sourceforge.net/projects/mysql-python/files/mysql-python/](http://sourceforge.net/projects/mysql-python/files/mysql-python/)
  * If you are using PyPy try the pure Python version: [http://dev.mysql.com/downloads/connector/python/](http://dev.mysql.com/downloads/connector/python/)
  * Install ujson from [http://www.lfd.uci.edu/~gohlke/pythonlibs/#ujson](http://www.lfd.uci.edu/~gohlke/pythonlibs/#ujson)
  * Download from Github:

 		git clone https://github.com/klahnakoski/pyLibrary.git

  * Download requirements:

		pip install -r requirements.txt
