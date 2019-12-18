from heilung.models.event import Event


class CampaignLaunched(Event):
    """Model of an campaignLaunched event
    """

    def __init__(self, round: int):
        """Create an campaignLaunched event object

        Arguments:
            round {int} -- Round the event first occurred in
        """
        super().__init__("campaignLaunched", round)
