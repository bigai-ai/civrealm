"""
    Freeciv-web - the web version of Freeciv. http://play.freeciv.org/
    Copyright (C) 2009-2015  The Freeciv-web project

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

TRUE = True
FALSE = False

TRI_NO = 0
TRI_YES = 1
TRI_MAYBE = 2

MAX_NUM_ITEMS = 200
MAX_LEN_NAME = 48
MAX_LEN_CITYNAME = 50

FC_INFINITY = (1000 * 1000 * 1000)

ACTIVITY_IDLE = 0
ACTIVITY_POLLUTION = 1
ACTIVITY_MINE = 3
ACTIVITY_IRRIGATE = 4
ACTIVITY_FORTIFIED = 5
ACTIVITY_SENTRY = 7
ACTIVITY_PILLAGE = 9
ACTIVITY_GOTO = 10
ACTIVITY_EXPLORE = 11
ACTIVITY_TRANSFORM = 12
ACTIVITY_FORTIFYING = 15
ACTIVITY_FALLOUT = 16
ACTIVITY_BASE = 18  # /* building base */
ACTIVITY_GEN_ROAD = 19
ACTIVITY_CONVERT = 20
ACTIVITY_LAST = 21  # /* leave this one last */

IDENTITY_NUMBER_ZERO = 0

# /* Corresponds to the enum action_target_kind */
ATK_CITY = 0
ATK_UNIT = 1
ATK_UNITS = 2
ATK_TILE = 3
ATK_SELF = 4
ATK_COUNT = 5

# /* Actions */
# ACTION_ESTABLISH_EMBASSY = 0
# ACTION_ESTABLISH_EMBASSY_STAY = 1
# ACTION_SPY_INVESTIGATE_CITY = 2
# ACTION_INV_CITY_SPEND = 3
# ACTION_SPY_POISON = 4
# ACTION_SPY_POISON_ESC = 5
# ACTION_SPY_STEAL_GOLD = 6
# ACTION_SPY_STEAL_GOLD_ESC = 7
# ACTION_SPY_SABOTAGE_CITY = 8
# ACTION_SPY_SABOTAGE_CITY_ESC = 9
# ACTION_SPY_TARGETED_SABOTAGE_CITY = 10
# ACTION_SPY_TARGETED_SABOTAGE_CITY_ESC = 11
# ACTION_SPY_STEAL_TECH = 12
# ACTION_SPY_STEAL_TECH_ESC = 13
# ACTION_SPY_TARGETED_STEAL_TECH = 14
# ACTION_SPY_TARGETED_STEAL_TECH_ESC = 15
# ACTION_SPY_INCITE_CITY = 16
# ACTION_SPY_INCITE_CITY_ESC = 17
# ACTION_TRADE_ROUTE = 18
# ACTION_MARKETPLACE = 19
# ACTION_HELP_WONDER = 20
# ACTION_SPY_BRIBE_UNIT = 21
# ACTION_SPY_SABOTAGE_UNIT = 22
# ACTION_SPY_SABOTAGE_UNIT_ESC = 23
# ACTION_CAPTURE_UNITS = 24
# ACTION_FOUND_CITY = 25
# ACTION_JOIN_CITY = 26
# ACTION_STEAL_MAPS = 27
# ACTION_STEAL_MAPS_ESC = 28
# ACTION_BOMBARD = 29
# ACTION_SPY_NUKE = 30
# ACTION_SPY_NUKE_ESC = 31
# ACTION_NUKE = 32
# ACTION_DESTROY_CITY = 33
# ACTION_EXPEL_UNIT = 34
# ACTION_RECYCLE_UNIT = 35
# ACTION_DISBAND_UNIT = 36
# ACTION_HOME_CITY = 37
# ACTION_UPGRADE_UNIT = 38
# ACTION_PARADROP = 39
# ACTION_AIRLIFT = 40
# ACTION_ATTACK = 41
# ACTION_CONQUER_CITY = 42
# ACTION_HEAL_UNIT = 43
ACTION_ESTABLISH_EMBASSY = 0
ACTION_ESTABLISH_EMBASSY_STAY = 1
ACTION_SPY_INVESTIGATE_CITY = 2
ACTION_INV_CITY_SPEND = 3
ACTION_SPY_POISON = 4
ACTION_SPY_POISON_ESC = 5
ACTION_SPY_STEAL_GOLD = 6
ACTION_SPY_STEAL_GOLD_ESC = 7
ACTION_SPY_SABOTAGE_CITY = 8
ACTION_SPY_SABOTAGE_CITY_ESC = 9
ACTION_SPY_TARGETED_SABOTAGE_CITY = 10
ACTION_SPY_TARGETED_SABOTAGE_CITY_ESC = 11
ACTION_SPY_SABOTAGE_CITY_PRODUCTION = 12
ACTION_SPY_SABOTAGE_CITY_PRODUCTION_ESC = 13
ACTION_SPY_STEAL_TECH = 14
ACTION_SPY_STEAL_TECH_ESC = 15
ACTION_SPY_TARGETED_STEAL_TECH = 16
ACTION_SPY_TARGETED_STEAL_TECH_ESC = 17
ACTION_SPY_INCITE_CITY = 18
ACTION_SPY_INCITE_CITY_ESC = 19
ACTION_TRADE_ROUTE = 20
ACTION_MARKETPLACE = 21
ACTION_HELP_WONDER = 22
ACTION_SPY_BRIBE_UNIT = 23
ACTION_CAPTURE_UNITS = 24
ACTION_SPY_SABOTAGE_UNIT = 25
ACTION_SPY_SABOTAGE_UNIT_ESC = 26
ACTION_FOUND_CITY = 27
ACTION_JOIN_CITY = 28
ACTION_STEAL_MAPS = 29
ACTION_STEAL_MAPS_ESC = 30
ACTION_SPY_NUKE = 31
ACTION_SPY_NUKE_ESC = 32
ACTION_NUKE = 33
ACTION_NUKE_CITY = 34
ACTION_NUKE_UNITS = 35
ACTION_DESTROY_CITY = 36
ACTION_EXPEL_UNIT = 37
ACTION_DISBAND_UNIT_RECOVER = 38
ACTION_DISBAND_UNIT = 39
ACTION_HOME_CITY = 40
ACTION_HOMELESS = 41
ACTION_UPGRADE_UNIT = 42
ACTION_CONVERT = 43
ACTION_AIRLIFT = 44
ACTION_ATTACK = 45
ACTION_SUICIDE_ATTACK = 46
ACTION_STRIKE_BUILDING = 47
ACTION_STRIKE_PRODUCTION = 48
ACTION_CONQUER_CITY = 49
ACTION_CONQUER_CITY2 = 50
ACTION_CONQUER_CITY3 = 51
ACTION_CONQUER_CITY4 = 52
ACTION_BOMBARD = 53
ACTION_BOMBARD2 = 54
ACTION_BOMBARD3 = 55
ACTION_BOMBARD_LETHAL = 56
ACTION_FORTIFY = 57
ACTION_CULTIVATE = 58
ACTION_PLANT = 59
ACTION_TRANSFORM_TERRAIN = 60
ACTION_ROAD = 61
ACTION_IRRIGATE = 62
ACTION_MINE = 63
ACTION_BASE = 64
ACTION_PILLAGE = 65
ACTION_CLEAN_POLLUTION = 66
ACTION_CLEAN_FALLOUT = 67
ACTION_TRANSPORT_BOARD = 68
ACTION_TRANSPORT_BOARD2 = 69
ACTION_TRANSPORT_BOARD3 = 70
ACTION_TRANSPORT_DEBOARD = 71
ACTION_TRANSPORT_EMBARK = 72
ACTION_TRANSPORT_EMBARK2 = 73
ACTION_TRANSPORT_EMBARK3 = 74
ACTION_TRANSPORT_EMBARK4 = 75
ACTION_TRANSPORT_DISEMBARK1 = 76
ACTION_TRANSPORT_DISEMBARK2 = 77
ACTION_TRANSPORT_DISEMBARK3 = 78
ACTION_TRANSPORT_DISEMBARK4 = 79
ACTION_TRANSPORT_LOAD = 80
ACTION_TRANSPORT_LOAD2 = 81
ACTION_TRANSPORT_LOAD3 = 82
ACTION_TRANSPORT_UNLOAD = 83
ACTION_SPY_SPREAD_PLAGUE = 84
ACTION_SPY_ATTACK = 85
ACTION_CONQUER_EXTRAS = 86
ACTION_CONQUER_EXTRAS2 = 87
ACTION_CONQUER_EXTRAS3 = 88
ACTION_CONQUER_EXTRAS4 = 89
ACTION_HUT_ENTER = 90
ACTION_HUT_ENTER2 = 91
ACTION_HUT_ENTER3 = 92
ACTION_HUT_ENTER4 = 93
ACTION_HUT_FRIGHTEN = 94
ACTION_HUT_FRIGHTEN2 = 95
ACTION_HUT_FRIGHTEN3 = 96
ACTION_HUT_FRIGHTEN4 = 97
ACTION_HEAL_UNIT = 98
ACTION_HEAL_UNIT2 = 99
ACTION_PARADROP = 100
ACTION_PARADROP_CONQUER = 101
ACTION_PARADROP_FRIGHTEN = 102
ACTION_PARADROP_FRIGHTEN_CONQUER = 103
ACTION_PARADROP_ENTER = 104
ACTION_PARADROP_ENTER_CONQUER = 105
ACTION_WIPE_UNITS = 106
ACTION_SPY_ESCAPE = 107
ACTION_UNIT_MOVE = 108
ACTION_UNIT_MOVE2 = 109
ACTION_UNIT_MOVE3 = 110
ACTION_CLEAN = 111
ACTION_TELEPORT = 112
ACTION_GAIN_VETERANCY = 113
ACTION_USER_ACTION1 = 114
ACTION_USER_ACTION2 = 115
ACTION_USER_ACTION3 = 116
ACTION_USER_ACTION4 = 117
ACTION_COUNT = 118  # The index needs to be updated if new actions are added in the future

# /* The action_decision enum */
# /* Doesn't need the player to decide what action to take. */
ACT_DEC_NOTHING = 0
# /* Wants a decision because of something done to the actor. */
ACT_DEC_PASSIVE = 1
# /* Wants a decision because of something the actor did. */
ACT_DEC_ACTIVE = 2

# /* The kind of universals_u (value_union_type was req_source_type).
# * Used in the network protocol. */
VUT_NONE = 0
VUT_ADVANCE = 1
VUT_GOVERNMENT = 2
VUT_IMPROVEMENT = 3
VUT_TERRAIN = 4
VUT_NATION = 5
VUT_UTYPE = 6
VUT_UTFLAG = 7
VUT_UCLASS = 8
VUT_UCFLAG = 9
VUT_OTYPE = 10
VUT_SPECIALIST = 11
VUT_MINSIZE = 12  # /* Minimum size: at city range means city size */
VUT_AI_LEVEL = 13  # /* AI level of the player */
VUT_TERRAINCLASS = 14  # /* More generic terrain type, currently "Land" or "Ocean" */
VUT_MINYEAR = 15
VUT_TERRAINALTER = 16  # /* Terrain alterations that are possible */
VUT_CITYTILE = 17  # /* Target tile is used by city. */
VUT_GOOD = 18
VUT_TERRFLAG = 19
VUT_NATIONALITY = 20
VUT_ROADFLAG = 21
VUT_EXTRA = 22
VUT_TECHFLAG = 23
VUT_ACHIEVEMENT = 24
VUT_DIPLREL = 25
VUT_MAXTILEUNITS = 26
VUT_STYLE = 27
VUT_MINCULTURE = 28
VUT_UNITSTATE = 29
VUT_MINMOVES = 30
VUT_MINVETERAN = 31
VUT_MINHP = 32
VUT_AGE = 33
VUT_NATIONGROUP = 34
VUT_TOPO = 35
VUT_IMPR_GENUS = 36
VUT_ACTION = 37
VUT_MINTECHS = 38
VUT_EXTRAFLAG = 39
VUT_MINCALFRAG = 40
VUT_SERVERSETTING = 41
VUT_CITYSTATUS = 42
VUT_MINFOREIGNPCT = 43
VUT_ACTIVITY = 44
VUT_DIPLREL_TILE = 45
VUT_DIPLREL_TILE_O = 46
VUT_DIPLREL_UNITANY = 47
VUT_DIPLREL_UNITANY_O = 48
VUT_MINLATITUDE = 49
VUT_MAXLATITUDE = 50
VUT_COUNTER = 51
VUT_ORIGINAL_OWNER = 52
VUT_IMPR_FLAG = 53
VUT_WRAP = 54
VUT_COUNT = 55  # /* Keep this last. */

# /* Freeciv's gui_type enum */
# /* Used for options which do not belong to any gui. */
GUI_STUB = 0
GUI_GTK2 = 1
GUI_GTK3 = 2
GUI_GTK3_22 = 3
# /* GUI_SDL remains for now for keeping client options alive until
# * user has migrated them to sdl2-client */
GUI_SDL = 4
GUI_QT = 5
GUI_SDL2 = 6
GUI_WEB = 7
GUI_GTK3x = 8

# /* Sometimes we don't know (or don't care) if some requirements for effect
# * are currently fulfilled or not. This enum tells lower level functions
# * how to handle uncertain requirements.
# */
RPT_POSSIBLE = 0  # /* We want to know if it is possible that effect is active */
RPT_CERTAIN = 1  # /* We want to know if it is certain that effect is active  */

O_FOOD = 0
O_SHIELD = 1
O_TRADE = 2
O_GOLD = 3
O_LUXURY = 4
O_SCIENCE = 5

# /* vision_layer enum */
V_MAIN = 0
V_INVIS = 1
V_SUBSURFACE = 2
V_COUNT = 3

# /* The unit_orders enum from unit.h */
ORDER_MOVE = 0
ORDER_ACTIVITY = 1
ORDER_FULL_MP = 2
ORDER_ACTION_MOVE = 3
ORDER_PERFORM_ACTION = 4
ORDER_LAST = 5

# /* The unit_ss_data_type enum from unit.h */
USSDT_QUEUE = 0
USSDT_UNQUEUE = 1
USSDT_BATTLE_GROUP = 2

SSA_NONE = 0
SSA_AUTOSETTLER = 1
SSA_AUTOEXPLORE = 2
SSA_COUNT = 3

packet_server_join_req = 4
packet_authentication_reply = 7
packet_nation_select_req = 10
packet_player_ready = 11
packet_edit_scenario_desc = 14
packet_chat_msg_req = 26
packet_city_sell = 33
packet_city_buy = 34
packet_city_change = 35
packet_city_worklist = 36
packet_city_make_specialist = 37
packet_city_make_worker = 38
packet_city_change_specialist = 39
packet_city_rename = 40
packet_city_options_req = 41
packet_city_refresh = 42
packet_city_name_suggestion_req = 43
packet_player_phase_done = 52
packet_player_rates = 53
packet_player_change_government = 54
packet_player_research = 55
packet_player_tech_goal = 56
packet_player_attribute_block = 57
packet_player_attribute_chunk = 58
packet_unit_sscs_set = 71
packet_unit_orders = 73
packet_unit_autosettlers = 74
packet_unit_load = 75
packet_unit_unload = 76
packet_unit_action_query = 82
packet_unit_type_upgrade = 83
packet_unit_do_action = 84
packet_unit_get_actions = 87
packet_conn_pong = 89
packet_diplomacy_init_meeting_req = 95
packet_diplomacy_cancel_meeting_req = 97
packet_diplomacy_create_clause_req = 99
packet_diplomacy_remove_clause_req = 101
packet_diplomacy_accept_treaty_req = 103
packet_diplomacy_cancel_pact = 105
packet_report_req = 111
packet_client_info = 119

packet_spaceship_launch = 135
packet_spaceship_place = 136
packet_single_want_hack_req = 160
packet_save_scenario = 181
packet_vote_submit = 189
packet_edit_mode = 190
packet_edit_recalculate_borders = 197
packet_edit_check_tiles = 198
packet_edit_toggle_fogofwar = 199
packet_edit_tile_terrain = 200
packet_edit_tile_extra = 202
packet_edit_startpos = 204
packet_edit_startpos_full = 205
packet_edit_tile = 206
packet_edit_unit_create = 207
packet_edit_unit_remove = 208
packet_edit_unit_remove_by_id = 209
packet_edit_unit = 210
packet_edit_city_create = 211
packet_edit_city_remove = 212
packet_edit_city = 213
packet_edit_player_create = 214
packet_edit_player_remove = 215
packet_edit_player = 216
packet_edit_player_vision = 217
packet_edit_game = 218
packet_unit_change_activity = 222
packet_worker_task = 241
packet_player_multiplier = 242
packet_client_heartbeat = 254
packet_goto_path_req = 257
packet_info_text_req = 259
