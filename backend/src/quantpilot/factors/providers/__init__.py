"""因子 provider 适配层."""

from quantpilot.factors.providers.base import BaseFactorProvider
from quantpilot.factors.providers.core_crypto import CoreCryptoFactorProvider
from quantpilot.factors.providers.external_crypto import ExternalCryptoFactorProvider
from quantpilot.factors.providers.registry import FactorProviderRegistry

__all__ = [
    "BaseFactorProvider",
    "CoreCryptoFactorProvider",
    "ExternalCryptoFactorProvider",
    "FactorProviderRegistry",
]
