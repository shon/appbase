from setuptools import setup, find_packages

setup(
    name='appbase',
    version='0.7.1',
    url="https://bitbucket.com/shon/appbase",
    classifiers=[
        'Programming Language :: Python',
        ],
    include_package_data=True,
    description='Helps develop python applications',
    long_description=open("README.rst").read(),
    packages=find_packages(),
    install_requires=[
        'blinker',
        'jsonschema',
        'gevent',
        'peewee==2.10.2',
        'psycopg2',
        'psycogreen',
        'flask',
        'html2text',
        'redis',
        'arnold',
        'requests_oauthlib'
      ],
    author='Shekhar Tiwatne',
    author_email='pythonic@gmail.com',
    license="http://www.opensource.org/licenses/mit-license.php",
    test_suite="tests",
    )
