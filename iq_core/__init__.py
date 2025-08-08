"""
IQ Option Trading System - Domain-driven architecture.
Sistema de Trading para IQ Option baseado em arquitetura orientada ao domínio (DDD).

This package provides a domain-driven architecture implementation
for an IQ Option trading system.

Este pacote implementa uma arquitetura orientada ao domínio
para um sistema de trading na IQ Option.
"""

__version__ = "1.0.9"
__description__ = "IQ Option API Wrapper"
__author__ = "Célio Junior"


from . import anotations, entities, exceptions, services, websocket

from .anotations import *
from .entities import *
from .exceptions import *
from .services import *
from .websocket import *

__all__ = []
__all__.extend(anotations.__all__)
__all__.extend(entities.__all__)
__all__.extend(exceptions.__all__)
__all__.extend(services.__all__)
__all__.extend(websocket.__all__)
