"""
Trinity: A universal framework for predicting phase transitions.

The Trinity Formula identifies critical transitions across diverse domains
using three fundamental dimensions (Surface, Depth, Time) and their interactions.
"""

__version__ = '0.1.0'
__author__ = 'Trinity Team'
__email__ = 'team@trinity-framework.org'

from .core import Model, TrinityModel
from .domains import DomainMapper, domains

__all__ = [
    'Model',
    'TrinityModel', 
    'DomainMapper',
    'domains',
    '__version__',
]
