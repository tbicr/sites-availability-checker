import re

from setuptools import find_packages, setup


setup(
    name="sites-availability-checker",
    version="0.1",
    author="Paveł Tyślacki",
    author_email="pavel.tyslacki@gmail.com",
    license="MIT",
    url="https://github.com/tbicr/sites-availability-checker",
    description="Site availability checker",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages(exclude=["tests*"]),
    python_requires="==3.8",
    install_requires=[r for l in open("requirements.txt").readlines() if (r := re.sub(r"#.*", "", l).strip())],
)
