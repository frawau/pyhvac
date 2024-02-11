#!/usr/bin/python3
import subprocess
from pathlib import Path
from setuptools import setup, find_packages, Command
from setuptools.dist import Distribution
from setuptools.command.build_py import build_py


BUILDIR = Path(__file__).parent
LIBDIR = BUILDIR / "IRremoteESP8266"
PYTHONDIR = LIBDIR / "python"
CPFILES = ["irhvac.py", "_irhvac.so"]
CPTOLOCATION = BUILDIR / "pyhvac"

with open("pyhvac/__init__.py") as f:
    exec(f.read())

with open("README", "r") as fh:
    long_description = fh.read()


class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""

    def has_ext_modules(self):
        return True


class BuildPyCommand(build_py):
    """Custom build command."""

    def run(self):
        self.run_command("clone_build")
        build_py.run(self)


class GitCloneAndBuild(Command):
    """Custom command to clone a git repository and build the needed files."""

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global LIBDIR
        global CPFILES
        global PYTHONDIR
        # Replace with your actual repository URL
        repo_url = "https://github.com/frawau/IRremoteESP8266"
        # Replace with your desired destination directory

        subprocess.run(["git", "clone", repo_url, LIBDIR])

        # Replace with your build commands specific to make and swig
        subprocess.run(["make"], cwd=PYTHONDIR)
        # Replace with your source and destination paths
        for f in CPFILES:
            rf = PYTHONDIR / f
            if not rf.exists():
                raise Exception("Could not build library.")
            rf.rename(CPTOLOCATION / f)
        # Clean up
        for p in LIBDIR.iterdir():
            if p.is_dir():
                rmtree(p)
            else:
                p.unlink()

        LIBDIR.rmdir()


setup(
    name="pyhvac",
    version=__version__,
    author="François Wautier",
    author_email="francois@wautier.eu",
    url="http://github.com/frawau/pyhvac",
    description="Python liberary/Utility to generate A/C IR signals",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "gaccode = pyhvac.__main__:main",
            "gcpanasonic = pyhvac.plugins.panasonic:main",
            "gcdaikin = pyhvac.plugins.daikin:main",
            "gclg = pyhvac.plugins.lg:main",
            "gcsharp = pyhvac.plugins.sharp:main",
        ],
    },
    packages=["pyhvac", "pyhvac.plugins"],
    package_data={"pyhvac": ["_irhvac.so"]},
    distclass=BinaryDistribution,
    cmdclass={
        "clone_build": GitCloneAndBuild,
        "build_py": BuildPyCommand,
    },
)
