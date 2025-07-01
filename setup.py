# -*- coding: utf-8 -*-

import io
import os
from setuptools import find_packages, setup

# Package meta-data.
NAME = "mnitjflowmeter"
DESCRIPTION = "MNITJFlowMeter - Network Flow Analysis Tool"
URL = "https://github.com/yourusername/mnitjflowmeter"
EMAIL = "sip@mnit.ac.in"
AUTHOR = "MNIT SIP"
REQUIRES_PYTHON = ">=3.8.0"
VERSION = "1.0.0"  # Directly set the version here


def get_requirements(source: str = "requirements.txt"):
    requirements = []
    with open(source) as f:
        for line in f:
            package, _, comment = line.partition("#")
            package = package.strip()
            if package:
                requirements.append(package)

    return requirements


REQUIRED = get_requirements("requirements.txt")

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Read the project's long description from README.md
long_description = DESCRIPTION
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
    
    # Try to append CHANGELOG.md if it exists
    try:
        with io.open(os.path.join(here, "CHANGELOG.md"), encoding="utf-8") as f:
            long_description += "\n\n" + f.read()
    except FileNotFoundError:
        pass
except FileNotFoundError:
    pass

# Set version directly
about = {"__version__": VERSION}

# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    project_urls={
        'Documentation': 'https://github.com/yourusername/mnitjflowmeter',
        'Source': 'https://github.com/yourusername/mnitjflowmeter',
        'Bug Reports': 'https://github.com/yourusername/mnitjflowmeter/issues',
    },
    python_requires=REQUIRES_PYTHON,
    entry_points={
        "console_scripts": ["mnitjflowmeter=mnitjflowmeter.sniffer:main"],
    },
    install_requires=REQUIRED,
    include_package_data=True,
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
