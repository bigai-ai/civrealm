# Copyright (C) 2023  The Freeciv-gym project
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

import threading
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from time import sleep

from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger


class CivMonitor():
    def __init__(self, host, user_name, poll_interval=4):
        self._driver = None
        self._poll_interval = poll_interval
        self._initiated = False
        self._host = host
        self._user_name = user_name
        self.monitor_thread = None
        self.state = "go_multi_player_and_join"
        self.start_observe = False

    def _observe_game(self, user_name):
        if not self._initiated:
            self._driver = webdriver.Firefox()
            self._driver.maximize_window()
            self._driver.get(f'http://{self._host}:8080/game/list?v=multiplayer')
            sleep(10)
            self._initiated = True

        if self._initiated:
            t = threading.currentThread()
            while getattr(t, "do_run", True):
                if self.state == "go_multi_player_and_join":
                    try:
                        bt_single_game = self._driver.find_elements(By.CSS_SELECTOR, "#multiplayer-table .highlight .label")[1]  # play [join]
                        bt_single_game.click()
                        sleep(self._poll_interval)
                        bt_single_game = self._driver.find_elements(By.CSS_SELECTOR, ".label.label-success")[0]  # join, You can join this game now
                        bt_single_game.click()
                        self.state = "input_observer_name"
                    except Exception as err:
                        self._driver.find_element("xpath", "/html/body/nav/div/div[2]/ul/li[2]/a").click()
                        sleep(self._poll_interval)
                        bt_single_games = self._driver.find_element("xpath",
                                                                    "/html/body/div/div/ul/li[2]/a")  # select multiplayer
                        bt_single_games.click()
                        sleep(self._poll_interval)
                        fc_logger.info("go_multi_player_and_join err! %s" % err)
                    sleep(self._poll_interval)

                if self.state == "input_observer_name":
                    try:
                        bt_single_game = self._driver.find_element(By.ID, "username_req")
                        bt_single_game.clear()
                        bt_single_game.send_keys("observer")
                        sleep(self._poll_interval)
                        bt_single_game = self._driver.find_elements(By.CSS_SELECTOR, ".ui-dialog-buttonset .ui-button.ui-corner-all.ui-widget")[1] # Join Games
                        bt_single_game.click()
                        self.state = "viewing"
                    except Exception as err:
                        fc_logger.info("input_observer_name err! %s" % err)
                    sleep(self._poll_interval)

                if self.state == "viewing":
                    try:
                        bt_single_game = self._driver.find_element(By.ID, "pregame_text_input")  # console
                        bt_single_game.clear()
                        bt_single_game.send_keys("/observe myagent")
                        sleep(self._poll_interval)
                        bt_single_game.send_keys(Keys.ENTER)
                        self.state = "view_game"
                    except Exception as err:
                        fc_logger.info("viewing err! %s" % err)
                    sleep(self._poll_interval)

                if (self.state == "view_game") and (self.start_observe == False):
                    self._driver.execute_script("center_tile_mapcanvas(tiles[Object.entries(units)[0][1].tile])")
                    self.start_observe = True
                    break
        #
        # if self._initiated:
        #     self._driver.close()

    def start_monitor(self):
        self.monitor_thread = threading.Thread(target=self._observe_game, args=[self._user_name])
        self.monitor_thread.start()

    def stop_monitor(self):
        self.monitor_thread.do_run = False
        self.monitor_thread.join()

    def take_screenshot(self, file_path):
        self._driver.save_screenshot(file_path)
