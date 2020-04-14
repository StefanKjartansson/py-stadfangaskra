# !/usr/bin/env python
import sys

import setuptools
from setuptools import find_packages, setup

requires = [
    "pandas>=1.0.3",
    "geopandas>=0.7.0",
]

extras = {
    "dev": ["ipython", "coverage", "pytest-cov", "pytest-env", "pytest", "pylint",],
    'dev:python_version>="3.6"': ["black"],
}

if int(setuptools.__version__.split(".", 1)[0]) < 18:
    if sys.version_info[0:2] < (3, 7):
        requires.append("dataclasses")
else:
    extras[":python_version<'3.7'"] = ["dataclasses"]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="py-stadfangaskra",
    description="Icelandic Location Registry utils",
    author="Stefán Kjartansson",
    author_email="stefan.mar.kjartansson@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests", "tests.*"]),
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    url="https://github.com/StefanKjartansson/py-stadfangaskra",
    install_requires=requires,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">=3.5",
    extras_require=extras,
)
