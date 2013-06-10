import os

from setuptools import setup, find_packages


root = os.path.abspath(os.path.dirname(__file__))
path = lambda *p: os.path.join(root, *p)


setup(
    name='pyLibrary',
    version=0.1,
    description='Library of Wonderful Things',
    long_description=open(path('README.md')).read(),
    author='Kyle Lahnakoski',
    author_email='kyle@lahnakoski.com',
    url='https://github.com/klahnakoski/pyLibrary',
    license='MPL 2.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False
)
