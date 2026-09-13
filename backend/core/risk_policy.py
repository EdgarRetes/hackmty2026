"""Versioned assumptions for the hackathon underwriting policy.

The rate is a dated Banco de México TIIE de Fondeo snapshot. It is not
fetched at request time so assessments remain reproducible and work offline.
"""

from datetime import date
from decimal import Decimal

POLICY_VERSION = "hackathon-v1"
REFERENCE_RATE = Decimal("0.0649000")
REFERENCE_RATE_AS_OF = date(2026, 9, 11)
REFERENCE_RATE_SOURCE = (
    "https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do"
    "?accion=consultarCuadro&idCuadro=CF111"
)
OPERATING_SPREAD = Decimal("0.0300000")
CAPITAL_MARGIN = Decimal("0.0200000")
MAX_ANNUALIZED_LOSS_SPREAD = Decimal("0.3000000")

# score ceiling, grade, one-year demo PD, advance fraction, demo LGD
RATING_BANDS = (
    (Decimal("20"), "A", Decimal("0.010000"), Decimal("0.900"), Decimal("0.300000")),
    (Decimal("35"), "B", Decimal("0.025000"), Decimal("0.850"), Decimal("0.350000")),
    (Decimal("50"), "C", Decimal("0.060000"), Decimal("0.750"), Decimal("0.450000")),
    (Decimal("65"), "D", Decimal("0.120000"), Decimal("0.600"), Decimal("0.550000")),
    (Decimal("100"), "E", Decimal("0.250000"), Decimal("0.000"), Decimal("0.700000")),
)
