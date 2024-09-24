from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="block_scoping",
    version="0.2.3",
    author="Romain Mouret",
    author_email="rom1mouret@gmail.com",
    description="A simple package for block scoping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rom1mouret/block_scoping",
    packages=find_packages(exclude=["tests"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        'console_scripts': [
            'check_block_scoping=block_scoping.check_files:main',
        ],
    },
    python_requires=">=3.5",
    test_suite="tests"
)