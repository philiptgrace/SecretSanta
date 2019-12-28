#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Secret Santa List Generator
===========================

Phil Grace, November 2018 and December 2019

`SecretSanta.py` parses the config YAML file and generates a Secret Santa list
according to the rules set by the user.

The central object in this program is `GivingMatrix`, which keeps track of
who the next person on the list could be. Entries are set to zero according to
a set of rules in the YAML file (which the user can turn on or off), and a
receiver is chosen for every giver with probabilities defined in the
`GivingMatrix`.
"""

# TODO:
# - Verify PeopleData is valid when reading in (history and partners are all spelled correctly)
# - Freeze into EXE using https://docs.python-guide.org/shipping/freezing/#py2exe or
#   https://stackoverflow.com/questions/2963263/how-can-i-create-a-simple-message-box-in-python and
#   https://www.flaticon.com/free-icon/santa-claus_290454
# - Docstrings, I guess.

import yaml
import sys
from random import choice, choices

class SecretSanta():
    def __init__(self):
        self.__PeopleData__ = self.get_people_data()
        self.__Names__ = list(self.__PeopleData__.keys())

        self.__Rules__ = self.read_yaml("rules")  # TODO: perform similar cleanup?
        self.__WeightHistory__ = self.__Rules__["WeightHistory"]
        self.__WeightCoupleHistory__ = self.__Rules__["WeightCoupleHistory"]
        self.__GrandfatherPeriod__ = self.__Rules__["GrandfatherPeriod"]
        self.__PartnerToPartnerAllowed__ = self.__Rules__["PartnerToPartner"]
        self.__AllowTriangles__ = self.__Rules__["Triangles"]
        self.__AllowCoupleToCouple__ = self.__Rules__["CoupleToCouple"]

        self.__OutputRules__ = self.read_yaml("output")  # TODO: perform similar cleanup?
        self.__PrintingOrder__ = self.__OutputRules__["PrintingOrder"]

        self.__Rigging__ = self.read_yaml("rigging")  # TODO: perform similar cleanup?


    def read_yaml(self, YAMLLabel):
        YAMLFileName = f"config/{YAMLLabel}.yaml"
        try:
            return yaml.safe_load(open(YAMLFileName, "r"))
        except yaml.YAMLError as e:
            sys.exit(f"Error in configuration file {YAMLFileName}: {e}")


    def get_people_data(self):
        """Read in `config/people.yaml` and perform some cleanup and validation of the data."""
        PeopleData = self.read_yaml("people")
        Names = PeopleData.keys()
        for Name in Names:
            if not PeopleData[Name]:
                PeopleData[Name] = {}
            if "Partner" not in PeopleData[Name].keys():
                PeopleData[Name]["Partner"] = None
            if "History" not in PeopleData[Name].keys():
                PeopleData[Name]["History"] = None

        # TODO: check for mispellings of couples and history names,
        #       check that the couples both point to each other

        return PeopleData


    def setup_giving_matrix(self):
        GivingMatrix = {Name: {Name: 1 for Name in self.__Names__} for Name in self.__Names__}

        for Giver, GiverData in self.__PeopleData__.items():
            # Remove self
            GivingMatrix[Giver][Giver] = 0

            # Remove partners
            GiverPartner = self.get_partner(Giver)
            if not self.__PartnerToPartnerAllowed__ and GiverPartner:
                GivingMatrix[Giver][GiverPartner] = 0

        GivingMatrix = self.weight_history(GivingMatrix)

        return GivingMatrix


    def select_starting_name(self):
        # Have a better chance of getting the list right if we start with one of
        # the rigged givers.
        if self.__Rigging__:
            return choice(list(self.__Rigging__.keys()))
        return choice(self.__Names__)


    def try_santas_list(self):
        """If one person has no viable givers, then will return `None`."""
        SantasList = []
        GivingMatrix = self.setup_giving_matrix()

        InitialGiver = self.select_starting_name()
        Giver = InitialGiver

        while len(SantasList) < len(self.__Names__):
            GivingMatrixRow = GivingMatrix[Giver]
            Receiver = self.select_receiver(Giver, GivingMatrixRow, InitialGiver, SantasList)
            if not Receiver:
                return

            SantasList.append((Giver, Receiver))

            # Remove this name from everyone's potential receivers, and remove
            # now-invalid combinations
            for Name in self.__Names__:
                GivingMatrix[Name][Receiver] = 0
            GivingMatrix = self.remove_triangles(Giver, GivingMatrix, SantasList)
            GivingMatrix = self.remove_couple_to_couple(Giver, GivingMatrix, SantasList)

            Giver = Receiver

        return SantasList


    def get_santas_list(self):
        MaxTries = 10000
        for i in range(MaxTries):
            SantasList = self.try_santas_list()
            if SantasList:
                return SantasList
        sys.exit(f"{MaxTries} iterations ran without finding a valid list!\nMaybe try loosening some of the rules in `config/rules.yaml`.")


    def get_giver(self, Receiver, SantasList):
        PairLookup = {Receiver: Giver for (Giver, Receiver) in SantasList}
        try:
            return PairLookup[Receiver]
        except KeyError:
            return


    def get_receiver(self, Giver, SantasList):
        PairLookup = {Giver: Receiver for (Giver, Receiver) in SantasList}
        try:
            return PairLookup[Giver]
        except KeyError:
            return


    def get_partner(self, Name):
        return self.__PeopleData__[Name]["Partner"]


    def select_receiver(self, Giver, GivingMatrixRow, InitialGiver, SantasList):
        """Returns `None` if no eligible receiver can be found."""
        # Don't allow the first giver to be a receiver until the list is almost complete
        if len(SantasList) < len(self.__Names__) - 1:
            GivingMatrixRow[InitialGiver] = 0

        PossibleReceivers = list(GivingMatrixRow.keys())
        ReceiverWeights = list(GivingMatrixRow.values())

        if self.__Rigging__ and Giver in self.__Rigging__.keys():
            return self.__Rigging__[Giver]

        if sum(ReceiverWeights):
            return choices(PossibleReceivers, ReceiverWeights)[0]


    def weight_history(self, GivingMatrix):
        for Giver, GiverData in self.__PeopleData__.items():
            if (self.__WeightHistory__ and GiverData["History"]):

                for HistoryDepth, HistoryReceiver in enumerate(GiverData["History"]):
                    if HistoryReceiver:
                        GivingMatrix[Giver][HistoryReceiver] = self.history_weighting_function(HistoryDepth, GivingMatrix[Giver][HistoryReceiver])

                        # Give the same weighting across couples if one member is part of the history
                        GiversPartner = self.get_partner(Giver)
                        ReceiversPartner = self.get_partner(HistoryReceiver)

                        if self.__WeightCoupleHistory__:
                            if ReceiversPartner:
                                GivingMatrix[Giver][ReceiversPartner] = self.history_weighting_function(HistoryDepth, GivingMatrix[Giver][ReceiversPartner])
                            if GiversPartner:
                                GivingMatrix[GiversPartner][HistoryReceiver] = self.history_weighting_function(HistoryDepth, GivingMatrix[GiversPartner][HistoryReceiver])
                            if GiversPartner and ReceiversPartner:
                                GivingMatrix[GiversPartner][ReceiversPartner] = self.history_weighting_function(HistoryDepth, GivingMatrix[GiversPartner][ReceiversPartner])

        return GivingMatrix


    def remove_couple_to_couple(self, Giver, GivingMatrix, SantasList):
        Receiver = self.get_receiver(Giver, SantasList)
        GiversPartner = self.get_partner(Giver)
        ReceiversPartner = self.get_partner(Receiver)

        if not self.__AllowCoupleToCouple__ and GiversPartner and ReceiversPartner:
            GivingMatrix[GiversPartner][ReceiversPartner] = 0

        return GivingMatrix


    def remove_triangles(self, Giver, GivingMatrix, SantasList):
        Receiver = self.get_receiver(Giver, SantasList)
        GiversPartner = self.get_partner(Giver)

        if not self.__AllowTriangles__ and GiversPartner:
            GivingMatrix[Receiver][GiversPartner] = 0

        return GivingMatrix


    def history_weighting_function(self, HistoryDepth, CurrentWeighting):
        try:
            return min((HistoryDepth/self.__GrandfatherPeriod__)**2, CurrentWeighting)
        except ZeroDivisionError:
            return 1


    def santas_list_to_string(self, SantasList):
        if self.__PrintingOrder__ == "ConfigOrder":
            SantasList = [(Giver, self.get_receiver(Giver, SantasList)) for Giver in self.__Names__]
        elif self.__PrintingOrder__ == "GivingOrder":
            pass
        elif self.__PrintingOrder__ == "AlphabeticalOrder":
            SantasList = sorted(SantasList)
        else:
            sys.exit("Please privide a giving order which is either 'ConfigOrder', 'GivingOrder', or 'AlphabeticalOrder'.")

        ListOfStrings = [f"{Giver} → {Receiver}" for Giver, Receiver in SantasList]
        return "\n".join(ListOfStrings)


    def print_list(self, SantasList):
        # TODO: make this a gui-type thing, http://easygui.sourceforge.net/
        SantasListString = self.santas_list_to_string(SantasList)
        print(SantasListString)


def main():
    Santa = SecretSanta()
    SantasList = Santa.get_santas_list()
    Santa.print_list(SantasList)

if __name__ == "__main__":
    main()
main()
