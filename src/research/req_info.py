'''
Created on 09.03.2018

@author: christian
'''

from utils.fc_types import TRI_NO, VUT_NONE, TRI_YES, VUT_ADVANCE,\
    VUT_GOVERNMENT, VUT_IMPROVEMENT, VUT_TERRAIN, VUT_NATION, VUT_UTYPE,\
    VUT_UTFLAG, VUT_UCLASS, VUT_UCFLAG, VUT_OTYPE, VUT_SPECIALIST, VUT_MINSIZE,\
    VUT_AI_LEVEL, VUT_TERRAINCLASS, VUT_MINYEAR, VUT_TERRAINALTER, VUT_CITYTILE,\
    VUT_GOOD, VUT_TERRFLAG, VUT_NATIONALITY, VUT_BASEFLAG, VUT_ROADFLAG,\
    VUT_EXTRA, VUT_TECHFLAG, VUT_ACHIEVEMENT, VUT_DIPLREL, VUT_MAXTILEUNITS,\
    VUT_STYLE, VUT_MINCULTURE, VUT_UNITSTATE, VUT_MINMOVES, VUT_MINVETERAN,\
    VUT_MINHP, VUT_AGE, VUT_NATIONGROUP, VUT_TOPO, VUT_IMPR_GENUS, VUT_ACTION,\
    VUT_MINTECHS, VUT_EXTRAFLAG, VUT_MINCALFRAG, VUT_SERVERSETTING, TRI_MAYBE,\
    RPT_POSSIBLE, VUT_COUNT

from utils.freecivlog import freelog
from research.tech_helpers import is_tech_known

"""
/* Range of requirements.
 * Used in the network protocol.
 * Order is important -- wider ranges should come later -- some code
 * assumes a total order, or tests for e.g. >= REQ_RANGE_PLAYER.
 * Ranges of similar types should be supersets, for example:
 *  - the set of Adjacent tiles contains the set of CAdjacent tiles,
 *    and both contain the center Local tile (a requirement on the local
 *    tile is also within Adjacent range)
 *  - World contains Alliance contains Player (a requirement we ourselves
 *    have is also within Alliance range). */
"""
REQ_RANGE_LOCAL = 0
REQ_RANGE_CADJACENT = 1
REQ_RANGE_ADJACENT = 2
REQ_RANGE_CITY = 3
REQ_RANGE_TRADEROUTE = 4
REQ_RANGE_CONTINENT = 5
REQ_RANGE_PLAYER = 6
REQ_RANGE_TEAM = 7
REQ_RANGE_ALLIANCE = 8
REQ_RANGE_WORLD = 9
REQ_RANGE_COUNT = 10  # /* keep this last */


class ReqCtrl():
    def __init__(self):
        pass
    @staticmethod
    def is_req_active(target_player, req, prob_type):
        """
          Checks the requirement to see if it is active on the given target.

          target gives the type of the target
          (player,city,building,tile) give the exact target
          req gives the requirement itself

          Make sure you give all aspects of the target when calling this function:
          for instance if you have TARGET_CITY pass the city's owner as the target
          player as well as the city itself as the target city.
        """

        result = TRI_NO
        """
          /* Note the target may actually not exist.  In particular, effects that
           * have a VUT_SPECIAL or VUT_TERRAIN may often be passed to this function
           * with a city as their target.  In this case the requirement is simply
           * not met. */
        """
        if req['kind'] == VUT_NONE:
            result = TRI_YES
        elif req['kind'] == VUT_ADVANCE:
            #/* The requirement is filled if the player owns the tech. */
            result = ReqCtrl.is_tech_in_range(target_player, req['range'], req['value'])
        elif req['kind'] in [VUT_GOVERNMENT, VUT_IMPROVEMENT, VUT_TERRAIN, VUT_NATION,
                             VUT_UTYPE, VUT_UTFLAG, VUT_UCLASS, VUT_UCFLAG, VUT_OTYPE,
                             VUT_SPECIALIST, VUT_MINSIZE, VUT_AI_LEVEL, VUT_TERRAINCLASS,
                             VUT_MINYEAR, VUT_TERRAINALTER, VUT_CITYTILE, VUT_GOOD, VUT_TERRFLAG,
                             VUT_NATIONALITY, VUT_BASEFLAG, VUT_ROADFLAG, VUT_EXTRA, VUT_TECHFLAG,
                             VUT_ACHIEVEMENT, VUT_DIPLREL, VUT_MAXTILEUNITS, VUT_STYLE,
                             VUT_MINCULTURE, VUT_UNITSTATE, VUT_MINMOVES, VUT_MINVETERAN,
                             VUT_MINHP, VUT_AGE, VUT_NATIONGROUP, VUT_TOPO, VUT_IMPR_GENUS,
                             VUT_ACTION, VUT_MINTECHS, VUT_EXTRAFLAG, VUT_MINCALFRAG,
                             VUT_SERVERSETTING]:

            #//FIXME: implement
            freelog("Unimplemented requirement type " + req['kind'])

        elif req['kind'] == VUT_COUNT:
            return False
        else:
            freelog("Unknown requirement type " + req['kind'])

        if result == TRI_MAYBE:
            return prob_type == RPT_POSSIBLE

        if req['present']:
            return result == TRI_YES
        else:
            return result == TRI_NO

    @staticmethod
    def are_reqs_active(target_player, reqs, prob_type):

        """
          Checks the requirement(s) to see if they are active on the given target.

          target gives the type of the target
          (player,city,building,tile) give the exact target

          reqs gives the requirement vector.
          The function returns TRUE only if all requirements are active.

          Make sure you give all aspects of the target when calling this function:
          for instance if you have TARGET_CITY pass the city's owner as the target
          player as well as the city itself as the target city.
        """

        for req in reqs:
            if not ReqCtrl.is_req_active(target_player, req, prob_type):
                return False
        return True

    @staticmethod
    def is_tech_in_range(target_player, trange, tech):
        """Is there a source tech within range of the target?"""

        if trange == REQ_RANGE_PLAYER:
            target = TRI_YES if is_tech_known(target_player, tech) else TRI_NO
            return target_player != None and target

        elif trange in [REQ_RANGE_TEAM, REQ_RANGE_ALLIANCE, REQ_RANGE_WORLD]:
            #/* FIXME: Add support for the above ranges. Freeciv's implementation
            #* currently (25th Jan 2017) lives in common/requirements.c */
            freelog("Unimplemented tech requirement range " + range)
            return TRI_MAYBE
        elif trange in [REQ_RANGE_LOCAL, REQ_RANGE_CADJACENT, REQ_RANGE_ADJACENT,
                        REQ_RANGE_CITY, REQ_RANGE_TRADEROUTE, REQ_RANGE_CONTINENT,
                        REQ_RANGE_COUNT]:

            freelog("Invalid tech req range " + range)
            return TRI_MAYBE
        else:
            return TRI_MAYBE