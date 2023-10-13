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

UNIT_TYPES = ['Settlers', 'Workers', 'Engineers', 'Warriors', 'Phalanx', 'Archers', 'Legion',
              'Pikemen', 'Musketeers', 'Partisan', 'Alpine Troops', 'Riflemen', 'Marines',
              'Paratroopers', 'Mech. Inf.', 'Horsemen', 'Chariot', 'Knights', 'Dragoons', 'Cavalry',
              'Armor', 'Catapult', 'Cannon', 'Artillery', 'Howitzer', 'Fighter', 'Bomber', 'Helicopter',
              'Stealth Fighter', 'Stealth Bomber', 'Trireme', 'Caravel', 'Galleon', 'Frigate',
              'Ironclad', 'Destroyer', 'Cruiser', 'AEGIS Cruiser', 'Battleship', 'Submarine',
              'Carrier', 'Transport', 'Cruise Missile', 'Nuclear', 'Diplomat', 'Spy', 'Caravan',
              'Freight', 'Explorer', 'Leader', 'Barbarian Leader', 'AWACS']

UNIT_COSTS = [40, 30, 40, 10, 20, 30, 40, 20, 30, 50, 50, 40, 60, 60, 50, 20, 30, 40, 50,
              60, 80, 40, 40, 50, 70, 60, 120, 100, 80, 160, 40, 40, 40, 50, 60, 60, 80,
              100, 160, 50, 160, 50, 60, 160, 30, 30, 50, 50, 30, 10, 40, 140]

UNIT_COST_DICT = dict(zip(UNIT_TYPES, UNIT_COSTS))


IMPR_TYPES = ['Airport', 'Aqueduct', 'Bank', 'Barracks', 'Barracks II', 'Barracks III', 'Cathedral',
              'City Walls', 'Coastal Defense', 'Colosseum', 'Courthouse', 'Factory', 'Granary', 'Harbor',
              'Hydro Plant', 'Library', 'Marketplace', 'Mass Transit', 'Mfg. Plant', 'Nuclear Plant',
              'Offshore Platform', 'Palace', 'Police Station', 'Port Facility', 'Power Plant',
              'Recycling Center', 'Research Lab', 'SAM Battery', 'SDI Defense', 'Sewer System',
              'Solar Plant', 'Space Component', 'Space Module', 'Space Structural', 'Stock Exchange',
              'Super Highways', 'Supermarket', 'Temple', 'University', 'Apollo Program', "A.Smith's Trading Co.",
              'Colossus', "Copernicus' Observatory", 'Cure For Cancer', "Darwin's Voyage", 'Eiffel Tower',
              'Great Library', 'Great Wall', 'Hanging Gardens', 'Hoover Dam', "Isaac Newton's College",
              "J.S. Bach's Cathedral", "King Richard's Crusade", "Leonardo's Workshop", 'Lighthouse',
              "Magellan's Expedition", 'Manhattan Project', "Marco Polo's Embassy", "Michelangelo's Chapel", 'Oracle',
              'Pyramids', 'SETI Program', "Shakespeare's Theater", 'Statue of Liberty', "Sun Tzu's War Academy",
              'United Nations', "Women's Suffrage", 'Coinage']

IMPR_COSTS = [120, 60, 80, 30, 30, 30, 80, 60, 60, 70, 60, 140, 40, 40, 180, 60,
              60, 120, 220, 120, 120, 70, 50, 60, 130, 140, 120, 70, 140, 80, 320,
              160, 320, 80, 120, 120, 80, 30, 120, 600, 400, 100, 200, 600, 300,
              100, 300, 300, 200, 600, 300, 400, 150, 400, 200, 400, 600, 200, 400,
              100, 200, 600, 200, 400, 300, 600, 600, 999]

IMPR_COST_DICT = dict(zip(IMPR_TYPES, IMPR_COSTS))
