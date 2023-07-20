"""
RCV results reporter for Dominion results files
"""

from setuptools import setup

setup(
    name='rcv-results',
    version='0.1',
    description='Ranked choice voting results reporter for Dominion results files',
    url='https://github.com/cjerdonek/dominion-rcv-results-reporter',
    author='Chris Jerdonek',
    author_email='chris.jerdonek@gmail.com',
    license='GPL',
    package_dir={
        '': 'src',
    },
    packages=['rcvresults'],
    # zip_safe=False,
)
