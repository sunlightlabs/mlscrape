import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "mlscrape",
    version = "0.1.0",
    author = "Andrew Pendleton",
    author_email = "apendleton@sunlightfoundation.com",
    description = "A library for learning site scraping strategies from user input",
    license = "BSD",
    keywords = "lxml ml requests svm liblinear",
    url = "http://github.com/sunlightlabs/mlscrape/",
    packages=find_packages(),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires = [
        "html2text",
        "requests",
        "gevent",
        "scrapelib",
        "lxml",
        "url>=0.1.3",
        "tgrocery>=0.1.4",
    ],
    dependency_links=[
        "git+https://github.com/seomoz/url-py.git#egg=url-0.1.3",
        "git+https://github.com/2shou/TextGrocery.git#egg=tgrocery-0.1.4",
    ],
)