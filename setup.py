from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the version from __init__.py
with open('ef_reverse_poco_generator/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip('"')
            break

setup(
    name="ef-reverse-poco-generator",
    version=version,
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to generate EF Core POCO classes from existing databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/howjerry/ef_reverse_poco_generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        "mysql-connector-python",
        "psycopg2-binary",
        "pyodbc",
        "jinja2",
    ],
    entry_points={
        "console_scripts": [
            "ef-reverse-poco=ef_reverse_poco_generator.main:main",
        ],
    },
)