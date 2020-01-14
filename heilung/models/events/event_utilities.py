from typing import List

from . import (AirportClosed, AntiVaccinationism, BioTerrorism,
               CampaignLaunched, ConnectionClosed, EconomicCrisis,
               ElectionsCalled, HygienicMeasuresApplied, InfluenceExerted,
               LargeScalePanic, MedicationAvailable, MedicationDeployed,
               MedicationInDevelopment, Outbreak, PathogenEncountered,
               Quarantine, Uprising, VaccineAvailable, VaccineDeployed,
               VaccineInDevelopment)

eventMap = {
    'airportClosed': AirportClosed,
    'antiVaccinationism': AntiVaccinationism,
    'bioTerrorism': BioTerrorism,
    'campaignLaunched': CampaignLaunched,
    'connectionClosed': ConnectionClosed,
    'economicCrisis': EconomicCrisis,
    'electionsCalled': ElectionsCalled,
    'hygienicMeasuresApplied': HygienicMeasuresApplied,
    'influenceExerted': InfluenceExerted,
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
