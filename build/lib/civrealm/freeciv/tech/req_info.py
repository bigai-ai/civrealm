# Copyright (C) 2023  The CivRealm project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

from civrealm.freeciv.utils.fc_types import TRI_NO, VUT_NONE, TRI_YES, VUT_ADVANCE,\
    VUT_GOVERNMENT, VUT_IMPROVEMENT, VUT_TERRAIN, VUT_NATION, VUT_UTYPE,\
    VUT_UTFLAG, VUT_UCLASS, VUT_UCFLAG, VUT_OTYPE, VUT_SPECIALIST, VUT_MINSIZE,\
    VUT_AI_LEVEL, VUT_TERRAINCLASS, VUT_MINYEAR, VUT_TERRAINALTER, VUT_CITYTILE,\
    VUT_GOOD, VUT_TERRFLAG, VUT_NATIONALITY, VUT_ROADFLAG,\
    VUT_EXTRA, VUT_TECHFLAG, VUT_ACHIEVEMENT, VUT_DIPLREL, VUT_MAXTILEUNITS,\
    VUT_STYLE, VUT_MINCULTURE, VUT_UNITSTATE, VUT_MINMOVES, VUT_MINVETERAN,\
    VUT_MINHP, VUT_AGE, VUT_NATIONGROUP, VUT_TOPO, VUT_IMPR_GENUS, VUT_ACTION,\
    VUT_MINTECHS, VUT_EXTRAFLAG, VUT_MINCALFRAG, VUT_SERVERSETTING, TRI_MAYBE,\
    RPT_POSSIBLE, VUT_COUNT

from civrealm.freeciv.tech.tech_helpers import is_tech_known
import civrealm.freeciv.tech.tech_const as tech_const
from civrealm.freeciv.utils.freeciv_logging import fc_logger


class ReqInfo():
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
            # /* The requirement is filled if the player owns the tech. */
            result = ReqInfo.is_tech_in_range(target_player, req['range'], req['value'])
        elif req['kind'] == VUT_GOVERNMENT:
            # /* The requirement is filled if the player is using the government. */
            if target_player == None:
                result = TRI_MAYBE
            else:
                result = TRI_YES if target_player['government'] == req['value'] else TRI_NO

        elif req['kind'] in [VUT_IMPROVEMENT, VUT_TERRAIN, VUT_NATION, VUT_UTYPE, VUT_UTFLAG, VUT_UCLASS, VUT_UCFLAG, VUT_OTYPE, VUT_SPECIALIST, VUT_MINSIZE, VUT_AI_LEVEL, VUT_TERRAINCLASS, VUT_MINYEAR, VUT_TERRAINALTER, VUT_CITYTILE, VUT_GOOD, VUT_TERRFLAG, VUT_NATIONALITY, VUT_ROADFLAG, VUT_EXTRA, VUT_TECHFLAG, VUT_ACHIEVEMENT, VUT_DIPLREL, VUT_MAXTILEUNITS, VUT_STYLE, VUT_MINCULTURE, VUT_UNITSTATE, VUT_MINMOVES, VUT_MINVETERAN, VUT_MINHP, VUT_AGE, VUT_NATIONGROUP, VUT_TOPO, VUT_IMPR_GENUS, VUT_ACTION, VUT_MINTECHS, VUT_EXTRAFLAG, VUT_MINCALFRAG, VUT_SERVERSETTING]:

            # //FIXME: implement
            fc_logger.warning("Unimplemented requirement type " + req['kind'])

        elif req['kind'] == VUT_COUNT:
            return False
        else:
            fc_logger.warning("Unknown requirement type " + req['kind'])

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
            if not ReqInfo.is_req_active(target_player, req, prob_type):
                return False
        return True

    @staticmethod
    def is_tech_in_range(target_player, trange, tech):
        """Is there a source tech within range of the target?"""

        if trange == tech_const.REQ_RANGE_PLAYER:
            target = TRI_YES if is_tech_known(target_player, tech) else TRI_NO
            return target_player != None and target

        elif trange in [tech_const.REQ_RANGE_WORLD, tech_const.REQ_RANGE_TEAM, tech_const.REQ_RANGE_ALLIANCE]:
            # /* FIXME: Add support for the above ranges. Freeciv's implementation
            # * currently (25th Jan 2017) lives in common/requirements.c */
            fc_logger.warning(f'Unimplemented tech requirement range {trange}')
            return TRI_MAYBE
        elif trange in [tech_const.REQ_RANGE_LOCAL, tech_const.REQ_RANGE_TILE, tech_const.REQ_RANGE_CADJACENT, tech_const.REQ_RANGE_ADJACENT, tech_const.REQ_RANGE_CITY, tech_const.REQ_RANGE_TRADEROUTE, tech_const.REQ_RANGE_CONTINENT, tech_const.REQ_RANGE_COUNT]:
            fc_logger.warning(f'Invalid tech req range {trange}')
            return TRI_MAYBE
        else:
            return TRI_MAYBE
