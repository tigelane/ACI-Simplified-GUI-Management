"""
ACIToolkit Installer using setuptools

This file fixes an issue with setuptools and the flask install.
"""
import os
from setuptools import setup


base_dir = os.path.dirname(__file__)

about = {}
with open(os.path.join(base_dir, "acitoolkit", "__about__.py")) as f:
    exec(f.read(), about)

setup(
    name=about["__title__"],
    version=about["__version__"],
    packages=["acitoolkit"],
    author=about["__author__"],
    author_email=about["__email__"],
    url=about["__uri__"],
    license=about["__license__"],
    install_requires=["requests",
                      "websocket-client>0.33.0",
                      "gitpython",
                      "flask-httpauth",
                      "flask-sqlalchemy",
                      "flask-admin",
                      "flask-bootstrap",
                      "flask-wtf",
                      "flask-cors",
                      "Flask>=0.10.1",
                      "pymysql",
                      "tabulate",
                      "py-radix",
                      "jsonschema",
                      "graphviz",
                      "ipaddress",
                      "deepdiff"],
    tests_requires=["mock"],
    description="This library allows basic Cisco ACI APIC configuration.",
)
