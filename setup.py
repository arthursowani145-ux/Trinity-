#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from README.md
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get version from __init__.py
about = {}
with open(os.path.join(here, 'trinity', '__init__.py'), encoding='utf-8') as f:
    exec(f.read(), about)

setup(
    name='trinity',
    version=about['__version__'],
    description='A universal framework for predicting phase transitions in complex systems',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/trinity-team/trinity',
    author='Trinity Team',
    author_email='team@trinity-framework.org',
    license='MIT',
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Security',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    
    keywords='phase-transitions critical-phenomena risk-modeling physics machine-learning finance security',
    
    packages=find_packages(exclude=['tests', 'tests.*', 'notebooks', 'scripts']),
    
    python_requires='>=3.8',
    
    install_requires=[
        'numpy>=1.20.0',
        'pandas>=1.3.0',
        'scipy>=1.7.0',
        'scikit-learn>=1.0.0',
        'matplotlib>=3.4.0',
        'pyyaml>=5.4.0',
    ],
    
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=22.0',
            'flake8>=4.0',
            'mypy>=0.950',
            'sphinx>=4.0',
            'sphinx-rtd-theme>=1.0',
        ],
        'notebooks': [
            'jupyter>=1.0',
            'seaborn>=0.11',
            'plotly>=5.0',
        ],
        'all': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=22.0',
            'flake8>=4.0',
            'mypy>=0.950',
            'sphinx>=4.0',
            'sphinx-rtd-theme>=1.0',
            'jupyter>=1.0',
            'seaborn>=0.11',
            'plotly>=5.0',
        ],
    },
    
    entry_points={
        'console_scripts': [
            'trinity-validate=trinity.scripts.validate:main',
            'trinity-calibrate=trinity.scripts.calibrate:main',
            'trinity-predict=trinity.scripts.predict:main',
            'trinity=trinity.cli:main',
        ],
    },
    
    project_urls={
        'Bug Reports': 'https://github.com/trinity-team/trinity/issues',
        'Source': 'https://github.com/trinity-team/trinity',
        'Documentation': 'https://trinity-framework.readthedocs.io',
        'Funding': 'https://github.com/sponsors/trinity-team',
    },
    
    include_package_data=True,
    package_data={
        'trinity': ['datasets/*.csv', 'configs/*.yaml'],
    },
    
    zip_safe=False,
)
