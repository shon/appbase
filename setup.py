from setuptools import setup, find_packages

setup(
    name='appbase',
    version='0.1.0',
    url="https://bitbucket.com/shon/appbase",
    classifiers=[
        'Programming Language :: Python',
        ],
    include_package_data=True,
    description='Helps develop python applications',
    long_description=open("README.rst").read(),
    packages=find_packages(),
    author='Shekhar Tiwatne',
    author_email='pythonic@gmail.com',
    license="http://www.opensource.org/licenses/mit-license.php",
    test_suite="tests",
    )

