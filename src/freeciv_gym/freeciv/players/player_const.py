# Government related
REPORT_WONDERS_OF_THE_WORLD = 0
REPORT_TOP_5_CITIES = 1
REPORT_DEMOGRAPHIC = 2
REPORT_ACHIEVEMENTS = 3

GOV_ANARCHY = 0
GOV_DESPOTISM = 1
GOV_MONARCHY = 2
GOV_COMMUNISM = 3
GOV_REPUBLIC = 4
GOV_DEMOCRACY = 5

GOV_TXT = {GOV_ANARCHY: "Anarchy", GOV_DESPOTISM: "Despotism",
           GOV_MONARCHY: "Monarchy", GOV_COMMUNISM: "Communism",
           GOV_REPUBLIC: "Republic", GOV_DEMOCRACY: "Democracy"}

# Diplomacy related
CLAUSE_ADVANCE = 0
CLAUSE_GOLD = 1
CLAUSE_MAP = 2
CLAUSE_SEAMAP = 3
CLAUSE_CITY = 4
CLAUSE_CEASEFIRE = 5
CLAUSE_PEACE = 6
CLAUSE_ALLIANCE = 7
CLAUSE_VISION = 8
CLAUSE_EMBASSY = 9

CLAUSE_TXT = ["Advance", "TradeGold", "ShareMap", "ShareSeaMap", "TradeCity",
              "Ceasefire", "Peace", "Alliance", "Vision", "Embassy"]

DS_ARMISTICE = 0
DS_WAR = 1
DS_CEASEFIRE = 2
DS_PEACE = 3
DS_ALLIANCE = 4
DS_NO_CONTACT = 5
DS_TEAM = 6
DS_LAST = 7

DS_TXT = ["Armistice", "War", "Ceasefire", "Peace", "Alliance", "No contact", "Team", "Last"]

# Player state related
MAX_NUM_PLAYERS = 30
MAX_AI_LOVE = 1000
# /* The plr_flag_id enum. */
PLRF_AI = 0
PLRF_SCENARIO_RESERVED = 1
PLRF_COUNT = 2
AI_SKILLS = ["Away", "Handicapped", "Novice", "Easy", "Normal", "Hard", "Cheating", "Experimental"]