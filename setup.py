#!/usr/bin/env python3
from __future__ import print_function
from setuptools import setup
from gcalcal import __VERSION__

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst',
                                        format='markdown_github',
                                        extra_args=("--wrap=none",))
except ImportError:
    import sys
    print('Warning: No long description generated.', file=sys.stderr)
    long_description = ''

author_emails = ['kaoru.konno@gmail']

setup(name='gcalcal',
      version=__VERSION__,
      author='kaoru.konno',
      author_email=', '.join(author_emails),
      maintainer='kaoru.konno',
      maintainer_email='kaoru.konno@gmail',
      description='gcallcli GUI',
      long_description=long_description,
      url='https://github.com/kaorin/gcalcal',
      license='MIT',
      script=['gcalcal'],
      data_files=[
        ('share/gcalcal/gcalcal.py', ['gcalcal.py']),
        ('share/gcalcal/gcalcal.glade', ['gcalcal.glade']),
        ('share/gcalcal/gcalcal.css', ['gcalcal.css']),
        ('share/gcalcal/sample.css', ['sample.css']),
        ('share/gcalcal/sample.jpg', ['sample.jpg']),
        ('share/applications',['gcalcal.desktop',])
      ],
      install_requires=[
          'gcalcli',
          'gobject',
      ],
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: GUI",
          "Intended Audience :: End Users/Desktop",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 3",
      ])
