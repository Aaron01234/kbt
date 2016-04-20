# coding=utf-8

__version__ = "1.0.0"

from entity import Entity
from spo import Spo
from data import KValue, Meta, Parser
from config import Config

# load parser
import parsers

# remove module
del entity
del spo
del data
del config
