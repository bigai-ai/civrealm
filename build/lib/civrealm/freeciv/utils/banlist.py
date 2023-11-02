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

class BanCtrl():
    def __init__(self):
        """
        /* This is a list of banned users of Freeciv-web.
           Note that user accounts can also be disabled by setting activated=0 in the auth DB table.
        """
        self.banned_users = []

    def check_text_with_banlist(self, text):
        """Returns false if the text contains a banned user."""
        if text == None or len(text) == 0:
            return False
        for user in self.banned_users:
            if user.toLower() in text.toLower():
                return False
        return True

    def check_text_with_banlist_exact(self, text):
        """Returns false if the text contains a banned user."""
        if text == None or len(text) == 0:
            return False
        for user in self.banned_users:
            if user.toLower() == text.toLower():
                return False
        return True
