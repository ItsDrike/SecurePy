from pathlib import Path

from setuptools import find_packages, setup

from securepy import config

DIR = Path(__file__).parent
README = (DIR / "README.md").read_text()

setup(
    name=config.NAME,
    version=config.VERSION,
    author=config.AUTHOR,
    author_email=config.AUTHOR_MAIL,
    description=config.DESCRIPTION,
    long_description=README,
    long_description_content_type="text/markdown",
    license=config.LICENCE,
    url="https://github.com/ItsDrike/SecurePy",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Topic :: System"
    ],
    packages=find_packages(exclude=("tests", "config")),
    include_package_data=True,
    install_requires=[],
    python_requires='>=3.7',
)
