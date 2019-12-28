Secret Santa List Generator
===========================
Phil Grace, November 2018 and December 2019.

`SecretSanta.py` parses the config file `config.yaml` and generates a Secret
Santa list according to the rules set by the user.

People: Define names, relationships, and history
------------------------------------------------

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

If we want to make sure Charlie gives to Sam and Jamie gives to Alex, then the rigging section of the config must be:
```
Rigging:
  Charlie: Sam
  Jamie: Alex
```

Setting rules for list
----------------------
The following rules can be set for the list generator:

* `WeightHistory` (`yes` or `no`)

  Does it matter who a person previously gave to?

* `WeightCoupleHistory` (`yes` or `no`)

  Factor couples into the history weighting?

* `GrandfatherPeriod` (positive number)

  So that we don't run out of combinations, history needs to matter less and
  less as time goes on. This variable chooses how many years until history is
  forgotten (5 is a good number, but will vary according to number of people
  involved).

* `PartnerToPartner` (`yes` or `no`)

  Can a person be paired with their partner?

* `Triangles` (`yes` or `no`)

  Can a person receive a gift from one person, and then give a gift to that
  person's partner?

* `CoupleToCouple` (`yes` or `no`)

  Can two couples be matched up with each other?

Setting output
--------------
The options for how the output should be produced are:

* `PrintingOrder` (one of `GivingOrder`, `ConfigOrder`, or `AlphabeticalOrder`)

  Defines how the list should be printed. The following optionsa are available:

  * `GivingOrder` prints in a chain of givers.
    ```
        Alex → Jamie
        Jamie → Sam
        Sam → Charlie
        Charlie → Alex
    ```
  * `ConfigOrder` prints in whatever order is listed in the config file.
    ```
        Jamie → Sam
        Sam → Charlie
        Alex → Jamie
        Charlie → Alex
    ```
  * `AlphabeticalOrder` prints alphabetically by giver.
    ```
        Alex → Jamie
        Charlie → Alex
        Jamie → Sam
        Sam → Charlie
    ```
