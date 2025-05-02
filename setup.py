from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="auto-doc-generator",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automated Code Documentation Generator for P&C Insurance",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/auto-doc-generator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "auto-doc=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "config/templates/*"],
    },
)