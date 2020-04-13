# !/usr/bin/env python

import setuptools
from setuptools import find_packages, setup

requires = [
    "pandas",
]

extras = {
    "dev": [
        "ipython",
        "black",
        "coverage",
        "pytest-cov",
        "pytest-env",
        "pytest",
        "pylint",
    ]
}

if int(setuptools.__version__.split(".", 1)[0]) < 18:
    if sys.version_info[0:2] < (3, 7):
        requires.append("dataclasses")
else:
    extras[":python_version<'3.7'"] = ["dataclasses"]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="stadfangaskra-utils",
    description="Icelandic Location Registry utils",
    author="Stefán Kjartansson",
    author_email="stefan.mar.kjartansson@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    url="https://github.com/StefanKjartansson/stadfangaskra-utils",
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
