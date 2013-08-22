from setuptools import setup

setup(
    name="dbeekeeper",
    version="1.0.0",
    test_suite='tests',
    install_requires=[
        "kazoo>=1.2.1",
        "zope.interface>=3.8.0",
    ],
)

