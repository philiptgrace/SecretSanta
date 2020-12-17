#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Brute Force Secret Santa List Generator
===========================

Phil Grace, December 2020
"""

from collections import deque
from itertools import permutations
from pathlib import Path
from time import time
import yaml


class NaughtyError(Exception):
    pass


class SecretSanta:
    _GivingMatrix = None

    def __init__(self):
        self._PeopleData = self.get_people_data()
        self.names = list(self._PeopleData.keys())

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

    @property
    def names(self):
        return self._names

    @names.setter
    def names(self, value):
        self._names = value

    def read_yaml(self, YAMLLabel):
        try:
            cwd = Path(__file__).resolve().parent
        except NameError:
            # Allow running in a script
            cwd = Path.cwd()

        YAMLFileName = cwd / "config" / f"{YAMLLabel}.yaml"
        try:
            with open(YAMLFileName, "r") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error in configuration file {YAMLFileName}") from e

    def get_people_data(self):
        return self.read_yaml("people")

    def brute_force(self):
        """"""
        # self.print_list(self.get_candidates())

    def print_list(self, SantasLists):
        for iList, SantaList in enumerate(SantasLists):
            print(f"==================== List {iList} ====================")
            for giver, receiver in self.list_to_pairs(SantaList):
                print(f"{giver} --> {receiver}")

    def get_candidates(self):
        for CandidateList in permutations(self.names):
            try:
                self.check_list(CandidateList)
                self.check_it_twice(CandidateList)
                yield CandidateList
            except NaughtyError:
                pass

    def get_partner(self, Name):
        try:
            return self._PeopleData[Name]["Partner"]
        except (TypeError, KeyError):
            return

    def get_history(self, giver):
        GiverData = self._PeopleData[giver]
        try:
            return GiverData["History"] or []
        except (TypeError, KeyError):
            return []

    @staticmethod
    def list_to_pairs(CandidateList):
        receivers = deque(CandidateList)
        receivers.rotate()
        # TODO: time how fast this is with and without `list`
        return list(zip(receivers, CandidateList))

    def check_list(self, CandidateList):
        pairs = self.list_to_pairs(CandidateList)

        self.check_partners_to_partners(pairs)
        self.check_previous_receiver(pairs)
        # TODO: Check couple to couple
        # TODO: Check triangles

    def compare_the_pairs(self, pairs, InvalidPairs):
        if any(InvalidPair in pairs for InvalidPair in InvalidPairs):
            raise NaughtyError

    def _get_partner_pairs(self):
        return [
            (giver, self.get_partner(giver))
            for giver in self.names
            if self.get_partner(giver)
        ]

    def check_partners_to_partners(self, pairs):
        """Check no partners giving to partners."""
        if self._PartnerToPartnerAllowed:
            pass

        PartnerPairs = self._get_partner_pairs()
        self.compare_the_pairs(pairs, PartnerPairs)

    def _get_history_pairs(self):
        return [
            (giver, self.get_history(giver)[0])
            for giver in self.names
            if (
                self.get_history(giver)
                and len(self.get_history(giver)) > 0
                and self.get_history(giver)[0]
            )
        ]

    def check_previous_receiver(self, pairs):
        """
        Check just the last person that a person gave to. All earlier receivers will be
        dealt with in the later list weighting stage.
        """
        if not self._WeightHistory or self._GrandfatherPeriod < 1:
            pass

        HistoryPairs = self._get_history_pairs()
        self.compare_the_pairs(pairs, HistoryPairs)

    def check_it_twice(self, CandidateList):
        """Function purely here for humour purposes."""


def main():
    t0 = time()
    Santa = SecretSanta()
    Santa.brute_force()
    print(f"{time()-t0:.2f}s to execute main().")


if __name__ == "__main__":
    main()

main()  # DELETE
