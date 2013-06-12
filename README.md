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

################################################################################
## MANY "PYTHON POWERED" NATIVE INSTALLS REQUIRE A POINTER TO THE PYTHON INSTALL
## BUT THEY HAVE NO IDEA WHERE TO LOOK ON A 64bit WINDOWS

## ALTER REGISTRY (SEE http://stackoverflow.com/questions/3652625/installing-setuptools-on-64-bit-windows)
## SET HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Python\PythonCore\2.7\InstallPath = "C:\Python27"

## INSTALL MySqldb 
## http://sourceforge.net/projects/mysql-python/files/mysql-python/