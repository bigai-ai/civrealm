'''
Created on 09.03.2018

@author: christian
'''
TECH_UNKNOWN = 0
TECH_PREREQS_KNOWN = 1
TECH_KNOWN = 2


def is_tech_known(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == TECH_KNOWN


def is_tech_unknown(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == TECH_UNKNOWN


def is_tech_prereq_known(pplayer, tech_id):
    return player_invention_state(pplayer, tech_id) == TECH_PREREQS_KNOWN


def player_invention_state(pplayer, tech_id):
    """
      Returns state of the tech for current pplayer.
      This can be: TECH_KNOWN, TECH_UNKNOWN, or TECH_PREREQS_KNOWN
      Should be called with existing techs or A_FUTURE

      If pplayer is None this checks whether any player knows the tech (used
      by the client).
    """
    if (pplayer is None) or ("inventions" not in pplayer) or tech_id >= len(pplayer["inventions"]):
        return TECH_UNKNOWN
    else:
        # /* Research can be None in client when looking for tech_leakage
        # * from player not yet received. */
        return int(pplayer['inventions'][tech_id])

    # /* FIXME: add support for global advances
    # if (tech != A_FUTURE and game.info.global_advances[tech_id]) {
    #  return TECH_KNOWN
    # } else {
    #  return TECH_UNKNOWN
    # }*/
