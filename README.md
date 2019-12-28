Secret Santa List Generator
===========================
Phil Grace, November 2018 and December 2019.

`SecretSanta.py` parses the config files in `config/` and generates a Secret
Santa list according to the rules set by the user.

People: Define names, relationships, and history
------------------------------------------------
The file `config/people.yaml` defines all the people involved in the Secret
Santa.

The syntax is simple: just a person's name, their partner (which can be left
blank or entirely omitted), and their history written in the form:
```
Sam:
  Partner: Charlie
  History:
    - Alex
    - Jamie
```
In this case, Sam had Alex the year before, and Jamie the year before that. If
someone wasn't involved in a particular year, leave that year as a blank entry
(but still put the dash there), _e.g._
```
Sam:
  Partner: Charlie
  History:
    - Alex
    -
    - Jamie
```

Rigging: Pre-define pairings of giver and receiver
--------------------------------------------------
`config/rigging.yaml` allows for pre-defined pairings to be implemented.

If we want to make sure Charlie gives to Sam and Jamie gives to Alex, then the rigging section of the config must be:
```
Charlie: Sam
Jamie: Alex
```

Setting rules for list
----------------------
The rules for how the list is to be produced are set in `config/rules.yaml`. The
following rules can be set:

* `WeightHistory` (`yes` or `no`)

  Does it matter who a person previously gave to?

* `WeightCoupleHistory` (`yes` or `no`)

  Shoudl couples be factored into the history weighting?

* `GrandfatherPeriod` (positive number)

  How many years should it be before giving history doesn't matter?

* `PartnerToPartner` (`yes` or `no`)

  Can a person be paired with their partner?

* `Triangles` (`yes` or `no`)

  If Sam receives a gift from Charlie, should they be allowed to give to
  Charlie's partner?

* `CoupleToCouple` (`yes` or `no`)

  Can one couple be matched to another couple?

Setting output
--------------
Finally, the output format options are defined in `config/output.yaml`. The
available options are:

* `PrintingOrder` (one of `GivingOrder`, `ConfigOrder`, or `AlphabeticalOrder`)

  Defines how the list should be printed. The following optionsa are available:

  * `GivingOrder` prints in a chain of givers. For instance,
    ```
    Alex → Jamie
    Jamie → Sam
    Sam → Charlie
    Charlie → Alex
    ```
  * `ConfigOrder` prints in whatever order is listed in the config file.
  * `AlphabeticalOrder` prints alphabetically by giver.
