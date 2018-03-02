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
ACTIVITY_BASE = 18			#/* building base */
ACTIVITY_GEN_ROAD = 19
ACTIVITY_CONVERT = 20
ACTIVITY_LAST = 21   #/* leave this one last */

IDENTITY_NUMBER_ZERO = 0

#/* Corresponds to the enum action_target_kind */
ATK_CITY  = 0
ATK_UNIT  = 1
ATK_UNITS = 2
ATK_TILE  = 3
ATK_SELF  = 4
ATK_COUNT = 5

#/* Actions */
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
ACTION_SPY_STEAL_TECH = 12
ACTION_SPY_STEAL_TECH_ESC = 13
ACTION_SPY_TARGETED_STEAL_TECH = 14
ACTION_SPY_TARGETED_STEAL_TECH_ESC = 15
ACTION_SPY_INCITE_CITY = 16
ACTION_SPY_INCITE_CITY_ESC = 17
ACTION_TRADE_ROUTE = 18
ACTION_MARKETPLACE = 19
ACTION_HELP_WONDER = 20
ACTION_SPY_BRIBE_UNIT = 21
ACTION_SPY_SABOTAGE_UNIT = 22
ACTION_SPY_SABOTAGE_UNIT_ESC = 23
ACTION_CAPTURE_UNITS = 24
ACTION_FOUND_CITY = 25
ACTION_JOIN_CITY = 26
ACTION_STEAL_MAPS = 27
ACTION_STEAL_MAPS_ESC = 28
ACTION_BOMBARD = 29
ACTION_SPY_NUKE = 30
ACTION_SPY_NUKE_ESC = 31
ACTION_NUKE = 32
ACTION_DESTROY_CITY = 33
ACTION_EXPEL_UNIT = 34
ACTION_RECYCLE_UNIT = 35
ACTION_DISBAND_UNIT = 36
ACTION_HOME_CITY = 37
ACTION_UPGRADE_UNIT = 38
ACTION_PARADROP = 39
ACTION_AIRLIFT = 40
ACTION_ATTACK = 41
ACTION_CONQUER_CITY = 42
ACTION_HEAL_UNIT = 43
ACTION_COUNT = 44

#/* The action_decision enum */
#/* Doesn't need the player to decide what action to take. */
ACT_DEC_NOTHING = 0
#/* Wants a decision because of something done to the actor. */
ACT_DEC_PASSIVE = 1
#/* Wants a decision because of something the actor did. */
ACT_DEC_ACTIVE = 2

#/* The kind of universals_u (value_union_type was req_source_type).
#* Used in the network protocol. */
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
VUT_MINSIZE = 12		#/* Minimum size: at city range means city size */
VUT_AI_LEVEL = 13		#/* AI level of the player */
VUT_TERRAINCLASS = 14	#/* More generic terrain type, currently "Land" or "Ocean" */
VUT_MINYEAR = 15
VUT_TERRAINALTER = 16      #/* Terrain alterations that are possible */
VUT_CITYTILE = 17          #/* Target tile is used by city. */
VUT_GOOD = 18
VUT_TERRFLAG = 19
VUT_NATIONALITY = 20
VUT_BASEFLAG = 21
VUT_ROADFLAG = 22
VUT_EXTRA = 23
VUT_TECHFLAG = 24
VUT_ACHIEVEMENT = 25
VUT_DIPLREL = 26
VUT_MAXTILEUNITS = 27
VUT_STYLE = 28
VUT_MINCULTURE = 29
VUT_UNITSTATE = 30
VUT_MINMOVES = 31
VUT_MINVETERAN = 32
VUT_MINHP = 33
VUT_AGE = 34
VUT_NATIONGROUP = 35
VUT_TOPO = 36
VUT_IMPR_GENUS = 37
VUT_ACTION = 38
VUT_MINTECHS = 39
VUT_EXTRAFLAG = 40
VUT_MINCALFRAG = 41
VUT_SERVERSETTING = 42
VUT_COUNT = 43             #/* Keep this last. */

#/* Freeciv's gui_type enum */
#/* Used for options which do not belong to any gui. */
GUI_STUB    = 0
GUI_GTK2    = 1
GUI_GTK3    = 2
GUI_GTK3_22 = 3
#/* GUI_SDL remains for now for keeping client options alive until
#* user has migrated them to sdl2-client */
GUI_SDL     = 4
GUI_QT      = 5
GUI_SDL2    = 6
GUI_WEB     = 7
GUI_GTK3x   = 8

#/* Sometimes we don't know (or don't care) if some requirements for effect
#* are currently fulfilled or not. This enum tells lower level functions
#* how to handle uncertain requirements.
#*/
RPT_POSSIBLE = 0 #/* We want to know if it is possible that effect is active */
RPT_CERTAIN = 1  #/* We want to know if it is certain that effect is active  */

O_FOOD = 0
O_SHIELD = 1
O_TRADE = 2
O_GOLD = 3
O_LUXURY = 4
O_SCIENCE = 5

#/* vision_layer enum */
V_MAIN = 0
V_INVIS = 1
V_SUBSURFACE = 2
V_COUNT = 3

#/* The unit_orders enum from unit.h */
ORDER_MOVE = 0
ORDER_ACTIVITY = 1
ORDER_FULL_MP = 2
ORDER_ACTION_MOVE = 3
ORDER_PERFORM_ACTION = 4
ORDER_LAST = 5

#/* The unit_ss_data_type enum from unit.h */
USSDT_QUEUE = 0
USSDT_UNQUEUE = 1
USSDT_BATTLE_GROUP = 2

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
