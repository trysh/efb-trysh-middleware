import os
import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 6):
    raise Exception("Python 3.6 or higher is required. Your version is %s." % sys.version)

version_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'efb_trysh_middleware/__version__.py')

__version__ = ""
exec(open(version_path).read())

long_description = open('README.rst').read()

setup(
    name='efb-trysh-middleware',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    version=__version__,
    description='trysh middleware for EH Forwarder Bot',
    long_description=long_description,
    author='trysh',
    author_email='s2s@s2s.app',
    url='https://github.com/trysh/efb-trysh-middleware',
    license='',  # ''AGPLv3+',
    include_package_data=True,
    python_requires='>=3.6',
    keywords=['ehforwarderbot', 'EH Forwarder Bot', 'EH Forwarder Bot Master Channel',
              'PGP', 'trysh', 'GnuPG'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications :: Chat",
        "Topic :: Utilities"
    ],
    install_requires=[
        "ehforwarderbot",
        "requests",
        # "python-gnupg"
    ],
    entry_points={
        "ehforwarderbot.middleware": "trysh.trysh = efb_trysh_middleware:TryshMiddleware"
    }
)
