import datetime
from dataclasses import dataclass


NETWORK_LEVELS = (
    "Niederspannung",
    "Umspannung in Niederspannung",
    "Mittelspannung",
    "Umspannung in Mittelspannung",
    "Hochspannung"
)


@dataclass
class DataManager:
    year: int = datetime.date.today().year
    date: datetime.date = datetime.date.today()

    company: str = ""
    address: str = ""
    market_location_id: str = ""        # Marktlokationsnummer

    producing: bool = False             # Unternehmen des produzierenden Gewerbes?
    power_supplier: bool = False        # Ist das Unternehmen Stromversorger im Sinne von § 4 StromStG?
    third_party_supply: bool = False    # Beliefert das Unternehmen Dritte mit Strom?

    network_operator: str = ""          # Name Verteilnetzbetreiber
    connection_level: str = ""          # Anschlussebene
    invoice_level: str = ""             # Abrechnungsebene (Abweichung bei singulärer Netznutzung)
    network_capacity: int = 0           # Vertragliche Netzanschlusskapazität (kW)
