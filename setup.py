#!/usr/bin/python
# coding: utf-8

"""
Tutorials on how to create a lib:
http://sametmax.com/creer-un-setup-py-et-mettre-sa-bibliotheque-python-en-ligne-sur-pypi/
http://peterdowns.com/posts/first-time-with-pypi.html
https://github.com/SolidCode/SolidPython/blob/master/setup.py
"""

from setuptools import setup, find_packages

with open("README.md") as fd:
    readme = fd.read()

with open("requirements.txt") as fd:
    install_requires = [l for l in fd.readlines()]

setup(
    name="chemscad",
    version="2.0.6",
    description="GUI application for the creation of Reactionware.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Cronin Group",
    author_email="croningp.pypi@gmail.com",
    url="https://github.com/croningp/chemscad",
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        'Operating System :: OS Independent'
    ],
    install_requires=install_requires,
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "chemscad=chemscad.main:main"
        ]
    }
)
