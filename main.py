#!/usr/bin/env python

import argparse
import random
import re
import time

from bs4 import BeautifulSoup
from psutil import process_iter

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class DevToFollower:

    """Dev.to automated follower.

    Attributes
    ----------
    driver : Selenium webdriver
        Web automation framework that allows you to execute your tests against different
        browsers.
    """

    def __init__(self, timeout=60):
        self._timeout = timeout
        self._closed = False

    def open_site(self, headless: bool = False) -> None:
        """Simple selenium webdriver to open a dev.to URL."""
        url = "https://dev.to/users/auth/twitter?callback_url=https://dev.to/users/auth/twitter/callback"
        options = Options()
        options.headless = headless
        profile = None

        self.driver = webdriver.Firefox(
            options=options, firefox_profile=profile, timeout=self._timeout
        )
        self.driver.get(url)

    def login(self, email_address: str, password: str) -> None:
        """Login onto dev.to via Twitter auth."""
        if not (email_address or password):
            raise RuntimeError("Missing email address or password.")
        form_xpath = '//*[@id="oauth_form"]'
        input_form = WebDriverWait(self.driver, self._timeout).until(
            EC.presence_of_element_located((By.XPATH, form_xpath))
        )
        username_form_id = "username_or_email"
        username_form_id_input = self.driver.find_element_by_id(username_form_id)
        username_form_id_input.send_keys(email_address)

        password_form_id = "password"
        password_form_id_input = self.driver.find_element_by_id(password_form_id)
        password_form_id_input.send_keys(password)
        password_form_id_input.send_keys(Keys.RETURN)
        time.sleep(5)

    def navigate_site(self) -> None:
        """Navigate through the website."""
        user_followers_url = "https://dev.to/dashboard/user_followers"
        self.driver.get(user_followers_url)
        action_cls_id = "action"
        WebDriverWait(self.driver, self._timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, action_cls_id))
        )

    def follow_users(self) -> None:
        """Iteratively follow following users."""
        self.navigate_site()
        followers = [
            name.text[1:]
            for name in self.page_source.findAll(
                "span", attrs={"class": "dashboard-username"}
            )
        ]
        for follower in followers:
            self.driver.get(f"https://dev.to/{follower}")
            follow_back_xpath = '//*[@id="user-follow-butt"]'
            status = ""
            retries = 5
            for i in range(retries):
                while True:
                    try:
                        status = WebDriverWait(self.driver, self._timeout).until(
                            EC.presence_of_element_located((By.XPATH, follow_back_xpath))
                        )
                        status = re.sub(r"[^\w]", "", status.text)
                        assert status
                    except BaseException:
                        continue
                    else:
                        break

            if status.upper() != "FOLLOWING":
                follow_back = self.driver.find_element_by_xpath(follow_back_xpath)
                follow_back.click()
                time.sleep(random.randint(3, 10))
                follow_back = self.driver.find_element_by_xpath(follow_back_xpath)
                follow_back = re.sub(r"[^\w]", "", follow_back.text)
                print(f"{follow_back} -> {follower}")
            followers.pop()

    @property
    def page_source(self) -> dict:
        """Get page source as object."""
        self._page_source = BeautifulSoup(self.driver.page_source, "html.parser")

        return self._page_source

    def close_session(self) -> None:
        """Close browser and cleanup"""
        if not self._closed:
            self.driver.close()
            self.driver.quit()
            time.sleep(1)

            PROCNAME = "geckodriver"
            _ = [proc.terminate() for proc in process_iter() if proc.name() == PROCNAME]
            self._closed = True


def main(args: dict) -> None:

    try:
        devto = DevToFollower()
        devto.open_site(True)
        devto.login(args.get("email_address"), args.get("password"))
        devto.navigate_site()
        devto.follow_users()
    except BaseException as err:
        print(f"An Exception ({str(err)!r}) occurred.")
        devto.close_session()
    else:
        devto.close_session()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "--password", "-p", dest="password", required=True, help="Dev.to Password"
    )
    parser.add_argument(
        "--email",
        "-e",
        dest="email_address",
        required=True,
        help=("Dev.to email address for logging in."),
    )
    args = vars(parser.parse_args())
    main(args)
