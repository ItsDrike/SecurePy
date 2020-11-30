from pathlib import Path
from setuptools import setup, find_packages
from config import config

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
        f"License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=("tests", "config")),
    include_package_data=True,
    install_requires=[],
    python_requires='>=3.7',
)

