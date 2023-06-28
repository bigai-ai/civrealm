# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import threading
from selenium import webdriver
from time import sleep

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger


class CivMonitor():
    def __init__(self, host, user_name, poll_interval=2):
        self._driver = None
        self._poll_interval = poll_interval
        self._initiated = False
        self._host = host
        self._user_name = user_name
        self.monitor_thread = None
        self.state = "review_games"
        self.start_observe = False

    def _observe_game(self, user_name):
        if not self._initiated:
            self._driver = webdriver.Firefox()
            self._driver.get(f'http://{self._host}:8080/')
            sleep(2)
            self._initiated = True

        bt_single_games = None
        bt_observe_game = None
        bt_start_observe = None

        if self._initiated:
            t = threading.currentThread()
            while getattr(t, "do_run", True):
                # Find single player button
                if self.state == "review_games":
                    try:
                        bt_single_games = self._driver.find_element("xpath", "/html/body/div/nav/div/div[2]/ul/li[2]/a")
                        bt_single_games.click()
                        self.state = "find_current_game"
                    except Exception as err:
                        fc_logger.info("Single Games Element not found! %s" % err)
                    sleep(self._poll_interval)

                if self.state == "find_current_game":
                    try:
                        bt_observe_game = self._driver.find_element(
                            "xpath", "/html/body/div/div/div/div[1]/table/tbody/tr[2]/td[7]/a[1]")
                        bt_observe_game.click()
                        self.state = "logon_game"
                    except Exception as err:
                        fc_logger.info("Observe Game Element not found! %s" % err)
                        bt_single_games = self._driver.find_element("xpath", "/html/body/nav/div/div[2]/ul/li[2]/a")
                        bt_single_games.click()
                    sleep(self._poll_interval)

                if self.state == "logon_game":
                    try:
                        inp_username = self._driver.find_element("xpath", "//*[@id='username_req']")
                        bt_start_observe = self._driver.find_element(
                            "xpath", "/html/body/div[contains(@class, 'ui-dialog')]/div[3]/div/button[1]")

                        inp_username.send_keys("")
                        inp_username.clear()
                        inp_username.send_keys('civmonitor')
                        bt_start_observe.click()
                        self.state = "view_game"
                    except Exception as err:
                        fc_logger.info("Username Element not found! %s" % err)
                    sleep(self._poll_interval)

                if self.state == "view_bot":
                    try:
                        players_tab = self._driver.find_element("xpath", "//*[@id='players_tab']")
                        players_tab.click()

                        players_table = self._driver.find_element(
                            "xpath", "/html/body/div[1]/div/div[4]/div/div[3]/div/table/tbody")

                        for row in players_table.find_elements("xpath", ".//tr"):
                            for td in row.find_elements("xpath", ".//td"):
                                if td.text.lower() == user_name.lower():
                                    td.click()
                                    break
                            else:
                                continue
                            break

                        bt_view_player = self._driver.find_element("xpath", "//*[@id='view_player_button']")
                        bt_view_player.click()
                        # state = "keep_silent"
                        self.state = "view_game"
                    except Exception as err:
                        fc_logger.info(err)
                    sleep(self._poll_interval)

                # if state == "keep_silent":
                #     sleep(self._poll_interval)
                if self.state == "view_game" and self.start_observe == False:
                    map_tab = self._driver.find_element("xpath", "//*[@id='map_tab']")
                    map_tab.click()
                    self.start_observe = True

        if self._initiated:
            self._driver.close()

    def start_monitor(self):
        self.monitor_thread = threading.Thread(target=self._observe_game, args=[self._user_name])
        self.monitor_thread.start()

    def stop_monitor(self):
        self.monitor_thread.do_run = False
        self.monitor_thread.join()
