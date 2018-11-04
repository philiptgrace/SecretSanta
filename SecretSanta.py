# Secret Santa List Generator
# Phil Grace November 2018
#
# SecretSanta.py parses the file config.yaml and generates a Secret Santa list
# according to the rules set by the user.
#
# The central object in this program is WeightingMatrix, which keeps track of
# who the next person on the list could be. Entries are set to zero according to
# a set of rules in the YAML file (which the user can turn on or off)

import yaml
import sys
from time import time
import numpy as np
from numpy.random import choice
from collections import OrderedDict

# Define some utility functions
def Person2Number(Name):
    return Names.index(Name)

def GetPartner(Name):
    CurrentInfo = NameData[Name]
    if 'Partner' in CurrentInfo and CurrentInfo['Partner'] != None:
        return CurrentInfo['Partner']
    else:
        return None

def GetGiver(Name):
    if SantasList.index(Name)>0 and Name in SantasList:
        Position = SantasList.index(Name)
        Giver = SantasList[Position-1]
    elif SantasList.index(Name)==0 and len(SantasList)==nNames and Name in SantasList:
        Giver = SantasList[-1]
    else:
        Giver = None

    return Giver

def GetReceiver(Name):
    if SantasList.index(Name)<nNames-1 and Name in SantasList:
        Position = SantasList.index(Name)
        Giver = SantasList[Position+1]
    elif SantasList.index(Name)==nNames-1 and Name in SantasList:
        Giver = SantasList[0]
    else:
        Giver = None

    return Giver

def GetHistory(Name):
    CurrentInfo = NameData[Name]
    if 'History' not in CurrentInfo or \
       CurrentInfo['History'] == None or \
           CurrentInfo['History'] == [] or \
               CurrentInfo['History'] == [None]:
        return None
    else:
        return CurrentInfo['History']

def WeightHistory(t, GrandfatherPeriod):
    # Can edit exponent to change functional form of weighting
    exp = 2.0

    if GrandfatherPeriod == 0:
        weighting = 1
    else:
        weighting = min((t/GrandfatherPeriod)**(exp), 1)
    return weighting

def RemoveChoice(CurrentName, InvalidName):
    global WeightingMatrix

    CurrentNumber = Person2Number(CurrentName)
    InvalidNumber = Person2Number(InvalidName)
    WeightingMatrix[CurrentNumber, InvalidNumber] = 0

def GrandfatherHistory(CurrentName):
    global WeightingMatrix
    
    CurrentNumber = Person2Number(CurrentName)
    History = GetHistory(CurrentName)
    
    if History != None:
        for HistoryDepth, HistoryName in enumerate(History):
            if HistoryName == None: continue

            HistoryNumber = Person2Number(HistoryName)
            HistoryWeighting = WeightHistory(HistoryDepth, GrandfatherPeriod)
            WeightingMatrix[CurrentNumber, HistoryNumber] = min(WeightingMatrix[CurrentNumber, HistoryNumber], HistoryWeighting)    # WeightingMatrix[CurrentNumber, HistoryNumber] = 

# Load file
try:
    config = yaml.safe_load(open('config.yaml', 'r'))
except yaml.YAMLError as e:
    print("Error in configuration file:", e)

# Read in rules
RuleDict = config['Rules']

IncludeHistory    = RuleDict['IncludeHistory']
GrandfatherPeriod = RuleDict['GrandfatherPeriod']
PartnerToPartner  = RuleDict['PartnerToPartner']
Triangles         = RuleDict['Triangles']
CoupleToCouple    = RuleDict['CoupleToCouple']

# Read in output specifications
OutputDict = config['Output']

PrintingOrder     = OutputDict['PrintingOrder']
WriteToFile       = OutputDict['WriteToFile']
PrintToScreen     = OutputDict['PrintToScreen']
Append            = OutputDict['Append']
assert PrintingOrder in ['GivingOrder', 'FamilyOrder', 'AlphabeticalOrder']

# Read in names
NameData = config['Names']
Names = list(config['Names'])

nNames = len(Names)

# Start the iterations
t0 = time()
Converged = False
nListFailed = 0
nListInvalid = 0

while not Converged:
    # WeightingMatrix[Jamie, Charlie] is the probability of Jamie giving to Charlie
    # We first remove all diagonal entries so people don't give to themselves
    WeightingMatrix = np.ones(nNames) - np.identity(nNames)

    StartingName = choice(Names)
    SantasList = [StartingName]

    CurrentName = StartingName

    for i in range(nNames-1):
        FinishedLoop = False   # Variable to handle breaks if list failes

        CurrentNumber = Person2Number(CurrentName)
        Partner = GetPartner(CurrentName)
        
        if Partner != None:
    
            # Don't let someone get matched with their partner
            if not PartnerToPartner:
                RemoveChoice(CurrentName, Partner)

            # Don't match two couples up
            if not PartnerToPartner:
                # First check if partner is already in list
                if Partner in SantasList:
                    ParnterPosition = SantasList.index(Partner)

                    # Check if the person they gave to has a partner
                    PartnersReceiver = SantasList[ParnterPosition+1]
                    PartnersReceiversPartner = GetPartner(PartnersReceiver)

                    # Now check if the person who gave to them has a partner
                    if ParnterPosition > 0:
                        PartnersGiver = SantasList[ParnterPosition-1]
                        PartnersGiversPartner = GetPartner(PartnersGiver)
                    else:
                        PartnersGiversPartner = None

                    # Exclude any pairing involving all four people
                    if PartnersReceiversPartner != None:
                        RemoveChoice(CurrentName, PartnersReceiversPartner)
                    if PartnersGiversPartner != None:
                        RemoveChoice(CurrentName, PartnersGiversPartner)
                    
        if not Triangles and len(SantasList)>1:
            Giver = SantasList[-2]
            GiversPartner = GetPartner(Giver)
            if GiversPartner != None:
                RemoveChoice(CurrentName, GiversPartner)
    
        # Weight history to be less important
        if IncludeHistory:
            GrandfatherHistory(CurrentName)
    
        # Blank out all previous names
        for PreviousName in SantasList:
            if not (PreviousName == StartingName and len(SantasList) == nNames):
                RemoveChoice(CurrentName, PreviousName)


        # Pick the next name from probability matrix
        p = WeightingMatrix[CurrentNumber,:]
    
        if sum(p) == 0: nListFailed += 1; break
        p /= sum(p)

        CurrentName = choice(Names, p=p)
        SantasList.append(CurrentName)

        FinishedLoop = True

    # Catch the program if it's really struggling to find a valid list
    if nListInvalid + nListFailed >= 100:
        print('Program took %-1.2fs to run.' % (time()-t0))
        sys.exit('100 iterations ran without finding a valid list!\nMaybe try loosening some of the rules in config.yaml.')

    # Final checks that final name is valid
    if FinishedLoop:
        ListValid = True

        StartPerson = SantasList[0]
        EndPerson = SantasList[-1]
        StartPartner = GetPartner(StartPerson)
        EndPartner = GetPartner(EndPerson)

        if not PartnerToPartner:
            if SantasList[-1] == GetPartner(SantasList[0]):
                ListValid = False
        if not Triangles:
            if GetReceiver(StartPerson) == EndPartner or GetGiver(EndPerson) == StartPartner: # Now broken (see latest output)
                ListValid = False
        if not CoupleToCouple:

            if StartPartner != None and EndPartner != None:
                if GetGiver(StartPartner) == EndPartner or \
                   GetGiver(EndPartner) == StartPartner:
                    ListValid = False

        # Check that the last person didn't have the first person last year
        if IncludeHistory:
            History = GetHistory(EndPerson)
            if History != None:
                if History[0] == StartPerson:
                    ListValid = False
        
        if ListValid:
            Converged = True
        else:
            nListInvalid += 1

print('Program took %-1.2fs to run.' % (time()-t0))
print('Completed successfully!')
print('Number of times a person had no options:     ', nListFailed)
print('Number of times a generated list was invalid:', nListInvalid)


# Print list
Givers = SantasList
Receivers = np.roll(SantasList, -1)
Pairings = [[Givers[i], Receivers[i]] for i in range(nNames)]

ListString = ''
# Print by order of names in SantasList
if PrintingOrder == 'GivingOrder':
    for i in range(nNames):
        ListString += '%s → %s\n' % (Pairings[i][0], '→', Pairings[i][1])

# Print by order of names in config.yaml
elif PrintingOrder == 'FamilyOrder':
    for Name in Names:
        for Pairing in Pairings:
            if Pairing[0] == Name:
                ListString += '%s → %s\n' % (Pairing[0], Pairing[1])

# Print names in alphabetical order
elif PrintingOrder == 'AlphabeticalOrder':
    for Name in sorted(Names):
        for Pairing in Pairings:
            if Pairing[0] == Name:
                ListString += '%s → %s\n' % (Pairing[0], Pairing[1])

# Print list to screen
if PrintToScreen:
    print()
    print(ListString)

# Write list to file
ListFileName = 'SecretSantaList.txt'

if Append:
    f = open(ListFileName, 'a+')
else:
    f = open(ListFileName, 'w')

if WriteToFile:
    f.write(ListString)
    f.write('\n'+20*'~'+2*'\n')
    f.close()
