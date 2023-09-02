#!/usr/bin/python3

from setuptools import setup, find_packages

with open("pyhvac/version.py") as f:
    exec(f.read())

ith open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pyhvac",
    version=__version__,
    author="François Wautier",
    author_email="francois@wautier.eu",
    url="http://github.com/frawau/pyhvac",
    description="Python liberary/Utility to generate A/C IR signals",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "hashlib",
    ],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "gaccode = pyhvac.__main__:main",
            "gcpanasonic = pyhvac.plugin.panasonic:main",
            "gcdaikin = pyhvac.plugin.daikin:main",
            "gclg = pyhvac.plugin.lg:main",
            "gcsharp = pyhvac.plugin.sharp:main",
        ],
    },
    packages=["pyhvac", "pyhvac.plugins"],
)
