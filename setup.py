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


def BuildSwig():
    buildswig=True
    resu = subprocess.run(["/usr/local/bin/swig", "-version"], stdout=subprocess.PIPE)
    for line in resu.stdout.decode().split("\n"):
        if "SWIG Version" in line:
            x = [ y.strip() for y in line.split(" ") if y.strip() ]
            if x[-1] >= "4.2.0":
                buildswig=False
                break
    if buildswig:
        haspkgmgr = False
        if not haspkgmgr:
            withme = subprocess.run(["which", "apt-get"], stdout=subprocess.PIPE, stderr = subprocess.DEVNULL).stdout.decode()
            if withme:
                haspkgmgr = True
                subprocess.run(["apt-get", "-y", "uninstall", "swig"])
                subprocess.run(["apt-get", "-y", "install", "libpcre2-dev","python3-dev"])
        if not haspkgmgr:
            withme = subprocess.run(["which", "yum"], stdout=subprocess.PIPE, stderr = subprocess.DEVNULL).stdout.decode()
            if withme:
                haspkgmgr = True
                subprocess.run(["yum","-y", "remove", "swig"])
                subprocess.run(["yum", "install", "-y", "pcre2-devel", "python3-devel"])
        if not haspkgmgr:
            withme = subprocess.run(["which", "apk"], stdout=subprocess.PIPE, stderr = subprocess.DEVNULL).stdout.decode()
            if withme:
                haspkgmgr = True
                subprocess.run(["apk","del", "swig"])
                subprocess.run(["apk", "add", "pcre2-devel", "python3-devel"])

        subprocess.run(["curl", "-L", "-o", "swig-4.2.0.tgz", "http://downloads.sourceforge.net/project/swig/swig/swig-4.2.0/swig-4.2.0.tar.gz"])
        subprocess.run(["tar", "xfz", "swig-4.2.0.tgz"])
        subprocess.run(["./configure"], cwd=BUILDIR / "swig-4.2.0")
        subprocess.run(["make"], cwd=BUILDIR / "swig-4.2.0")
        subprocess.run(["make","install"], cwd=BUILDIR / "swig-4.2.0")
        subprocess.run(["rm", "-rf", "swig-4.2.0*"])
        subprocess.run(["/usr/local/bin/swig", "-version"])

    # resu = subprocess.run(["ls", "-al", "/usr/include/"], stdout=subprocess.PIPE)
    # libname=""
    # for line in resu.stdout.decode().split("\n"):
    #     if "python3" in line:
    #         x = [ y.strip() for y in line.split(" ") if y.strip() ]
    #         libname = x[-1]
    #         break
    # if libname:
    #     subprocess.run(["mv", f"/usr/include/{libname}", "/usr/include/python"])
    # else:
    #     raise Exception("No python3 includes.")





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
        repo_url = "https://github.com/frawau/IRremoteESP8266"

        #TODO check if we nedd to do this
        BuildSwig()
        if not LIBDIR.exists():
            subprocess.run(["git", "clone", repo_url, LIBDIR])
        subprocess.run(["make"], cwd=PYTHONDIR)

        for f in CPFILES:
            rf = PYTHONDIR / f
            if not rf.exists():
                raise Exception("Could not build library.")
            rf.rename(CPTOLOCATION / f)
        subprocess.run(["make", "distclean"], cwd=PYTHONDIR)



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
