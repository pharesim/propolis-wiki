from setuptools import setup, find_packages

setup(
name='wiki',
version='0.1',
packages=find_packages(),
install_requires=[
'Flask',
'flask_session',
'beem',
],
)
