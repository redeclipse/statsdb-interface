#! /usr/bin/env python3

from setuptools import setup, find_packages


setup(
    name="statsdbinterface",
    version="2.0.0-alpha",
    description="Red Eclipse statistics database interface",
    url="https://github.com/red-eclipse/statsdb-interface-2",
    author="Beha",
    author_email="shacknetisp@users.noreply.github.com",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Flask>=0.10",
        "Flask-SQLAlchemy>=2.0",
        "tornado>=4.4.0",
    ],
)
