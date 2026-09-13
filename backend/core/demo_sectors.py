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
    "Distribuidora Regia": "retail_chain",
    "Aceros del Norte": "manufacturing",
    "TecnoSoluciones del Norte": "technology",
    "Grupo Constructor Peninsular": "construction",
    "Materiales Industriales MTY": "manufacturing",
    "Transportes Fronterizos": "logistics",
    "Insumos Médicos MTY": "pharma_retail",
    "Papelería Escolar MTY": "retail_chain",
    "Farmacias San Rafael": "pharma_retail",
    "Constructora Sierra Madre": "construction",
    "Textiles Cumbres": "textile",
    "Autotransportes del Golfo": "logistics",
    "AgroIndustrias Nuevo León": "agriculture",
    "Hotelera Regiomontana": "hospitality",
}

SPECIALIZED_SECTORS = {"retail_chain", "logistics"}


def sector_for_client(debtor_client):
    return CLIENT_SECTORS.get(debtor_client.name)
