"""
Demo-only industry sector labels per DebtorClient — independent of
DebtorClient.archetype, which encodes payment *behavior* (reliable /
irregular / delinquent / new), not industry. This only exists so the
specialized pricing agent has something to check sector membership
against; a real implementation would store this on the model instead of
a name-keyed lookup here.
"""

CLIENT_SECTORS = {
    "Comercializadora del Norte": "retail_chain",
    "Ferretería La Unión": "construction_supplies",
    "Grupo Constructor Peninsular": "construction",
    "Materiales Industriales MTY": "manufacturing",
    "Farmacias San Rafael": "pharma_retail",
    "Autotransportes del Golfo": "logistics",
}

SPECIALIZED_SECTORS = {"retail_chain", "logistics"}


def sector_for_client(debtor_client):
    return CLIENT_SECTORS.get(debtor_client.name)
