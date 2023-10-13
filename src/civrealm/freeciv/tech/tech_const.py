from civrealm.freeciv.utils.fc_types import MAX_NUM_ADVANCES

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
REQ_RANGE_TILE = 1
REQ_RANGE_CADJACENT = 2
REQ_RANGE_ADJACENT = 3
REQ_RANGE_CITY = 4
REQ_RANGE_TRADEROUTE = 5
REQ_RANGE_CONTINENT = 6
REQ_RANGE_PLAYER = 7
REQ_RANGE_TEAM = 8
REQ_RANGE_ALLIANCE = 9
REQ_RANGE_WORLD = 10
REQ_RANGE_COUNT = 11   #/* Keep this last */


"""
/* TECH_KNOWN is self-explanatory, TECH_PREREQS_KNOWN are those for which all
 * requirements are fulfilled all others (including those which can never
 * be reached) are TECH_UNKNOWN */
"""
TECH_UNKNOWN = 0
TECH_PREREQS_KNOWN = 1
TECH_KNOWN = 2


A_NONE = 0
A_FIRST = 1
A_LAST = MAX_NUM_ADVANCES + 1
A_UNSET = A_LAST + 1
A_FUTURE = A_LAST + 2
A_UNKNOWN = A_LAST + 3
A_LAST_REAL = A_UNKNOWN

A_NEVER = None
U_NOT_OBSOLETED = None

AR_ONE = 0
AR_TWO = 1
AR_ROOT = 2
AR_SIZE = 3


TF_BONUS_TECH = 0  # /* player gets extra tech if rearched first */
TF_BRIDGE = 1  # /* "Settler" unit types can build bridges over rivers */
TF_RAILROAD = 2  # /* "Settler" unit types can build rail roads */
TF_POPULATION_POLLUTION_INC = 3  # /* Increase the pollution factor created by population by one */
TF_FARMLAND = 4  # /* "Settler" unit types can build farmland */
TF_BUILD_AIRBORNE = 5  # /* Player can build air units */
TF_LAST = 6
