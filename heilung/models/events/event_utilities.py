from typing import List

from . import *

eventMap = {
    'airportClosed': AirportClosed,
    'antiVaccinationism': AntiVaccinationism,
    'bioTerrorism': BioTerrorism,
    'connectionClosed': ConnectionClosed,
    'economicCrisis': EconomicCrisis,
    'medicationDeployed': MedicationDeployed,
    'outbreak': Outbreak,
    'quarantine': Quarantine,
    'uprising': Uprising,
    'vaccineDeployed': VaccineDeployed,
    'medicationAvailable': MedicationAvailable,
    'largeScalePanic': LargeScalePanic,
    'medicationInDevelopment': MedicationInDevelopment,
    'pathogenEncountered': PathogenEncountered,
    'vaccineAvailable': VaccineAvailable,
    'vaccineInDevelopment': VaccineInDevelopment,
}

def convert_events(eventList: List[dict]) -> List[object]:
    """converts a list of events as dictionary to objects

    Arguments:
        eventList {List[dict]} -- List of events as provided in the request

    Returns:
        List[Event] -- List of Event objects
    """
    return [eventMap[event['type']].from_dict(event) for event in eventList]
