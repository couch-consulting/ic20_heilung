# Basic Playable CLI version of the game

from heilung.models.actions import EndRound, ApplyHygienicMeasures, ExertInfluence, LaunchCampaign, CallElections, \
    PutUnderQuarantine, CloseAirport, CloseConnection, DevelopVaccine, DeployVaccine, DevelopMedication, \
    DeployMedication
from heilung.models import City
from heilung.models.events.sub_event.pathogen import Pathogen


# Example for cli game [tip: adapt timeout of test program and copy paste possible answers] [warning: ui sucks]
# Put code below uncommented in server after the print of game state recap
# return play()

def play():
    print("\n Actions: \n "
          + "[Needed input without brackets] Name of Action [COST] \n"
          + "[0] EndRound [0] \n"
          + "[1,CityName] ApplyHygienicMeasures [3] \n"
          + "[2,CityName] ExertInfluence [3] \n"
          + "[3,CityName] LaunchCampaign [3] \n"
          + "[4,CityName] CallElections [3] \n"
          + "[5,CityName,num_rounds] PutUnderQuarantine [10*num_rounds+20] \n"
          + "[6,CityName,num_rounds] CloseAirport [5*num_rounds+15] \n"
          + "[7,FromCityName,ToCityName,num_rounds] CloseConnection [3*num_rounds+3] \n"
          + "[8,PathogenName] DevelopVaccine [40] \n"
          + "[9,CityName,PathogenName] DeployVaccine [5] \n"
          + "[10,PathogenName] DevelopMedication [20] \n"
          + "[11,CityName,PathogenName] DeployMedication [10] \n"
          )
    action_data = input("Choose an action: ")
    action_data = action_data.split(',')

    action_type = int(action_data[0])
    parameters = action_data[1:]

    if action_type == 0:
        return EndRound().build_action()
    if action_type == 1:
        city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        return ApplyHygienicMeasures(city).build_action()
    if action_type == 2:
        city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        return ExertInfluence(city).build_action()
    if action_type == 3:
        city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        return LaunchCampaign(city).build_action()
    if action_type == 4:
        city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        return CallElections(city).build_action()
    if action_type == 5:
        city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        num_rounds = int(parameters[1])
        return PutUnderQuarantine(city, num_rounds).build_action()
    if action_type == 6:
        city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        num_rounds = int(parameters[1])
        return CloseAirport(city, num_rounds).build_action()
    if action_type == 7:
        from_city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        to_city = City(parameters[1], "", "", "", "", "", "", "", "", [])
        num_rounds = int(parameters[2])
        return CloseConnection(from_city, to_city, num_rounds).build_action()
    if action_type == 8:
        pathogen = Pathogen(parameters[0], "", "", "", "")
        return DevelopVaccine(pathogen).build_action()
    if action_type == 9:
        city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        pathogen = Pathogen(parameters[1], "", "", "", "")
        return DeployVaccine(city, pathogen).build_action()
    if action_type == 10:
        pathogen = Pathogen(parameters[0], "", "", "", "")
        return DevelopMedication(pathogen).build_action()
    if action_type == 11:
        city = City(parameters[0], "", "", "", "", "", "", "", "", [])
        pathogen = Pathogen(parameters[1], "", "", "", "")
        return DeployMedication(city, pathogen).build_action()
