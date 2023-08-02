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
    license='BSD-3-Clause',
    package_dir={
        '': 'src',
    },
    packages=['rcvresults'],
    # zip_safe=False,
    python_requires='>=3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
)
