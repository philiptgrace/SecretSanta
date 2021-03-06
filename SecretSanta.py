#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Secret Santa List Generator
===========================

Phil Grace, November 2018, December 2019, December 2020

`SecretSanta.py` parses the config YAML file and generates a Secret Santa list
according to the rules set by the user.

The central object in this program is `GivingMatrix`, which keeps track of
who the next person on the list could be. Entries are set to zero according to
a set of rules in the YAML file (which the user can turn on or off), and a
receiver is chosen for every giver with probabilities defined in the
`GivingMatrix`.
"""

# TODO:
# - Verify PeopleData is valid when reading in (history and partners are all spelled
#   correctly)
# - Freeze into EXE using https://docs.python-guide.org/shipping/freezing/#py2exe
#   stackoverflow.com/questions/2963263/how-can-i-create-a-simple-message-box-in-python
#   https://www.flaticon.com/free-icon/santa-claus_290454
# - Turn into a webapp
# - Docstrings, I guess.

# TODO: implement logging
# TODO: write tests

import numpy as np
import pandas as pd
from pathlib import Path
from random import choice, choices
import yaml


class SecretSanta:
    _GivingMatrix = None

    def __init__(self):
        # FIXME
        self._PeopleData = self.get_people_data()
        self.names = list(self._PeopleData.keys())

        self.validate_people_data()

        # TODO: validate YAML input
        self._Rules = self.read_yaml("rules")
        self._WeightHistory = self._Rules["WeightHistory"]
        self._WeightCoupleHistory = self._Rules["WeightCoupleHistory"]
        self._GrandfatherPeriod = self._Rules["GrandfatherPeriod"]
        self._PartnerToPartnerAllowed = self._Rules["PartnerToPartner"]
        self._AllowTriangles = self._Rules["Triangles"]
        self._AllowCoupleToCouple = self._Rules["CoupleToCouple"]

        self._OutputRules = self.read_yaml("output")
        self._PrintingOrder = self._OutputRules["PrintingOrder"]

        self._Rigging = self.read_yaml("rigging")
        # TODO: implement blacklist

    @property
    def names(self):
        return self._names

    @names.setter
    def names(self, value):
        self._names = value

    @property
    def GivingMatrix(self):
        if self._GivingMatrix is None:
            # Set up giving matrix if not set up yet
            self._initialise_giving_matrix()
        return self._GivingMatrix

    @GivingMatrix.setter
    def GivingMatrix(self, matrix):
        self._GivingMatrix = matrix

    def update_matrix(self, giver, receiver, value):
        self._GivingMatrix[giver][receiver] = value

    def zero_entry(self, giver, receiver):
        self.update_matrix(giver, receiver, 0)

    def _initialise_giving_matrix(self):
        n = len(self.names)
        self._GivingMatrix = pd.DataFrame(
            np.ones([n, n]) - np.identity(n), columns=self.names, index=self.names,
        )

        for giver in self.names:
            # Remove partners
            partner = self.get_partner(giver)
            if not self._PartnerToPartnerAllowed and partner:
                self.zero_entry(giver, partner)

        self._GivingMatrix = self.weight_history(self._GivingMatrix)
        self._GivingMatrix = self.weight_couple_history(self._GivingMatrix)

        if self._Rigging:
            self.rig()

    def read_yaml(self, YAMLLabel):
        try:
            cwd = Path(__file__).resolve().parent
        except NameError:
            # Allow running in a script
            cwd = Path.cwd()

        YAMLFileName = cwd / "config" / f"{YAMLLabel}.yaml"
        try:
            return yaml.safe_load(open(YAMLFileName, "r"))
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error in configuration file {YAMLFileName}") from e

    def get_people_data(self):
        return self.read_yaml("people")

    def validate_people_data(self):
        # FIXME
        for name in self.names:
            # Validate partners
            partner = self.get_partner(name)
            if partner:
                if partner not in self.names:
                    raise ValueError(
                        "{name}'s partner not a recognised name: {partner}"
                    )
                if self.get_partner(partner) != name:
                    raise ValueError(
                        f"Error in `config/people.yaml`. {name} and {partner} are not "
                        "both listed as each others partner."
                    )

            # Validate histories
            history = self.get_history(name)
            UnknownNames = [
                receiver
                for receiver in filter(None, history)
                if receiver not in self.names
            ]
            if UnknownNames:
                raise ValueError(
                    f"Unknown people in {name}'s giving history: "
                    f"{', '.join(UnknownNames)}."
                )

    def try_santas_list(self):
        # FIXME
        # Force reinitialisation
        self._GivingMatrix = None

        SantasList = []

        InitialGiver = choice(self.names)
        giver = InitialGiver

        while len(SantasList) < len(self.names):
            GivingMatrixRow = self.GivingMatrix[giver]
            receiver = self.select_receiver(
                giver, GivingMatrixRow, InitialGiver, SantasList
            )
            if not receiver:
                raise RuntimeError(f"No viable receivers for {giver}.")

            SantasList.append((giver, receiver))

            # Remove this name from everyone's potential receivers, and remove
            # now-invalid combinations
            for name in self.names:
                self.zero_entry(name, receiver)
            self.GivingMatrix = self.remove_triangles(
                giver, self.GivingMatrix, SantasList
            )
            self.GivingMatrix = self.remove_couple_to_couple(
                giver, self.GivingMatrix, SantasList
            )

            giver = receiver

        return SantasList

    def get_santas_list(self):
        # FIXME
        MaxTries = 100000
        for i in range(MaxTries):
            try:
                return self.try_santas_list()
            except RuntimeError:
                pass

        raise RuntimeError(
            f"{MaxTries} iterations ran without finding a valid list!\n"
            "Maybe try loosening some of the rules in `config/rules.yaml`."
        )

    def get_giver(self, Receiver, SantasList):
        # FIXME
        PairLookup = {Receiver: Giver for (Giver, Receiver) in SantasList}
        try:
            return PairLookup[Receiver]
        except KeyError:
            return

    def get_receiver(self, Giver, SantasList):
        # FIXME
        PairLookup = {Giver: Receiver for (Giver, Receiver) in SantasList}
        try:
            return PairLookup[Giver]
        except KeyError:
            return

    def get_partner(self, Name):
        # FIXME
        try:
            return self._PeopleData[Name]["Partner"]
        except (TypeError, KeyError):
            return

    def select_receiver(self, Giver, GivingMatrixRow, InitialGiver, SantasList):
        # FIXME
        """Returns `None` if no eligible receiver can be found."""
        # Don't allow the first giver to be a receiver until the list is almost complete
        if len(SantasList) < len(self.names) - 1:
            GivingMatrixRow[InitialGiver] = 0

        PossibleReceivers = list(GivingMatrixRow.index)
        ReceiverWeights = list(GivingMatrixRow)

        if sum(ReceiverWeights):
            return choices(PossibleReceivers, ReceiverWeights)[0]

    def rig(self):
        # FIXME
        for giver, receiver in self._Rigging.items():
            for name in self.names:
                if name != receiver:
                    self.zero_entry(giver, name)

    def get_history(self, giver):
        # FIXME
        GiverData = self._PeopleData[giver]
        try:
            return GiverData["History"] or []
        except (TypeError, KeyError):
            return []

    def weight_history(self, GivingMatrix):
        # FIXME
        if not self._WeightHistory:
            return GivingMatrix

        weight = self.history_weighting_function
        for giver in self.names:
            history = self.get_history(giver)
            for depth, receiver in enumerate(history):
                if receiver:
                    self.update_matrix(
                        giver, receiver, weight(depth, GivingMatrix[giver][receiver])
                    )

        return GivingMatrix

    def weight_couple_history(self, GivingMatrix):
        # FIXME
        """
        Give the same weighting across couples if one member is part of the history.
        """

        if not (self._WeightHistory and self._WeightCoupleHistory):
            return GivingMatrix

        for giver in self.names:
            history = self.get_history(giver)
            for depth, receiver in enumerate(history):
                if not receiver:
                    continue

                weight = self.history_weighting_function
                GivingMatrix[giver][receiver] = weight(
                    depth, GivingMatrix[giver][receiver]
                )
                self.update_matrix(
                    giver, receiver, weight(depth, GivingMatrix[giver][receiver])
                )

                GiversPartner = self.get_partner(giver)
                ReceiversPartner = self.get_partner(receiver)

                if ReceiversPartner:
                    GivingMatrix[giver][ReceiversPartner] = weight(
                        depth, GivingMatrix[giver][ReceiversPartner]
                    )
                if GiversPartner:
                    GivingMatrix[GiversPartner][receiver] = weight(
                        depth, GivingMatrix[GiversPartner][receiver],
                    )
                if GiversPartner and ReceiversPartner:
                    GivingMatrix[GiversPartner][ReceiversPartner] = weight(
                        depth, GivingMatrix[GiversPartner][ReceiversPartner],
                    )

        return GivingMatrix

    def remove_couple_to_couple(self, Giver, GivingMatrix, SantasList):
        # FIXME
        Receiver = self.get_receiver(Giver, SantasList)
        GiversPartner = self.get_partner(Giver)
        ReceiversPartner = self.get_partner(Receiver)

        if not self._AllowCoupleToCouple and GiversPartner and ReceiversPartner:
            GivingMatrix[GiversPartner][ReceiversPartner] = 0

        return GivingMatrix

    def remove_triangles(self, Giver, GivingMatrix, SantasList):
        # FIXME
        Receiver = self.get_receiver(Giver, SantasList)
        GiversPartner = self.get_partner(Giver)

        if not self._AllowTriangles and GiversPartner:
            GivingMatrix[Receiver][GiversPartner] = 0

        return GivingMatrix

    def history_weighting_function(self, HistoryDepth, CurrentWeighting):
        # FIXME
        try:
            return min((HistoryDepth / self._GrandfatherPeriod) ** 2, CurrentWeighting)
        except ZeroDivisionError:
            return 1

    def santas_list_to_string(self, SantasList):
        # FIXME
        if self._PrintingOrder == "ConfigOrder":
            SantasList = [
                (Giver, self.get_receiver(Giver, SantasList)) for Giver in self.names
            ]
        elif self._PrintingOrder == "GivingOrder":
            pass
        elif self._PrintingOrder == "AlphabeticalOrder":
            SantasList = sorted(SantasList)
        else:
            raise ValueError(
                "Please privide a giving order which is either 'ConfigOrder', "
                "'GivingOrder', or 'AlphabeticalOrder'."
            )

        ListOfStrings = [f"{Giver} → {Receiver}" for Giver, Receiver in SantasList]
        return "\n".join(ListOfStrings)

    def print_list(self, SantasList):
        # FIXME
        # TODO: make this a gui-type thing, http://easygui.sourceforge.net/
        SantasListString = self.santas_list_to_string(SantasList)
        print(SantasListString)


def main():
    # FIXME
    Santa = SecretSanta()
    SantasList = Santa.get_santas_list()
    Santa.print_list(SantasList)


if __name__ == "__main__":
    main()

main()
