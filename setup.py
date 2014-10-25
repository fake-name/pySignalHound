
import setuptools
from distutils.core import setup
import sys
setup(
	# Application name:
	name="PySignalHound",

	# Version number (initial):
	version="0.0.1",

	# Application author details:
	author="Connor Wolf	",
	author_email="github@imaginaryindustries.com",

	# Packages
	packages=["SignalHound"],

	# Include additional files into the package
	include_package_data=True,

	# Put the `bb_api.dll` in the proper dll directory so it's available for loading.
	data_files=[(sys.prefix + "/DLLs", ["SignalHound/data/bb_api.dll"])],

	# Details
	url="http://pypi.python.org/pypi/MyApplication_v010/",

	#
	# license="LICENSE.txt",
	description="Wrapper for SignalHound spectrum analysers.",

	# long_description=open("README.txt").read(),

	# Dependent packages (distributions)
	install_requires=[
		"numpy",
	],
)