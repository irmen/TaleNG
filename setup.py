"""
Setup script for distutils

'Tale-NG' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""
import re
from setuptools import setup

with open("tale_ng/__init__.py") as version_file:
    # extract the VERSION definition from the tale package without importing it
    version_line = next(line for line in version_file if line.startswith("__version__"))
    tale_version = re.match(r"__version__\s?=\s?['\"](.+)['\"]", version_line).group(1)

print("version=" + tale_version)

setup(
    name='tale_ng',
    version=tale_version,
    author='Irmen de Jong',
    author_email='irmen@razorvine.net',
    license="LGPL3",
    description='Interactive Fiction, MUD & mudlib framework',
    # packages=['tale', 'tale.cmds', 'tale.items', 'tale.tio', 'tale.demo', 'tale.demo.zones', 'tale.web'],
    keywords="mud, mudlib, interactive fiction, text adventure",
    platforms="any",
    zip_safe=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Role-Playing",
        "Topic :: Games/Entertainment :: Multi-User Dungeons (MUD)"
    ],
    install_requires=["appdirs>=1.4", "smartypants>=2.0"],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    test_suite="tests"
)
