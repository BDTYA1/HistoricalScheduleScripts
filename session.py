import os
import re
import requests
import yaml
from datetime import datetime, timedelta, timezone
from http.cookiejar import DefaultCookiePolicy

CODE_ERROR = "Failed to get code for rotating cookies. Please provide new cookies"
ROTATE_COOKIES_PAGE = "https://accounts.google.com/RotateCookiesPage?origin=https://docs.google.com&og_pid=1"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

class DocsSession:
    def __init__(self, user_id=0):
        self._doc_html = ""
        self._next_rotation = None
        self._rotate_code_is_new = False
        self._url_prefix = ""

        self._session = requests.Session()
        self._session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
        self._user_id = user_id

        with open("credentials.yml", "r") as creds_file:
            creds_data = yaml.safe_load(creds_file)
            self._session.cookies.set("APISID", creds_data["apisid"])
            self._session.cookies.set("HSID", creds_data["hsid"])
            self._session.cookies.set("OSID", creds_data["osid"])
            self._session.cookies.set("SAPISID", creds_data["sapisid"])
            self._session.cookies.set("SID", creds_data["sid"])
            self._session.cookies.set("SSID", creds_data["ssid"])
            if "sidts" in creds_data:
                self._session.cookies.set("__Secure-1PSIDTS", creds_data["sidts"])
                self._rotate_cookies()

    def get(self, endpoint):
        if self._needs_rotating(): 
            self._rotate_cookies()
        return self._session.get(f"{self._url_prefix}{endpoint}")

    def get_info_token(self):
        if not hasattr(self, "_doc_html"):
            raise RuntimeError("Doc has not been loaded. Please call load_doc()")

        info_token = re.search(r"\"info_params\":{\"token\":\"(.*?)\"", self._doc_html)
        if not info_token:
            raise ValueError("Failed to get info token. Please provide new cookies")

        return info_token.group(1)

    def get_session_id(self):
        if not hasattr(self, "_doc_html"):
            raise RuntimeError("Doc has not been loaded. Please call load_doc()")

        session_id = re.search(r"mergedConfig = {\"id\":\"(.*?)\"", self._doc_html)
        if not session_id:
            raise ValueError("Failed to get session ID. Please provide new cookies")

        return session_id.group(1)

    def load_doc(self, doc_id):
        self._url_prefix = f"https://docs.google.com/spreadsheets/u/{self._user_id}/d/{doc_id}"

        r = self._session.get(f"{self._url_prefix}/edit")
        if not r.ok:
            raise RuntimeError(f"Sheet request failed: {r.content}")

        self._doc_html = r.text

    def _needs_rotating(self):
        return self._next_rotation and datetime.now(timezone.utc) >= self._next_rotation

    def _rotate_cookies(self):
        rotate_code=None

        if os.path.isfile("cookie_cache.yml"):
            with open("cookie_cache.yml", "r") as cc_file:
                cookie_cache = yaml.safe_load(cc_file)
                if datetime.now(timezone.utc) < datetime.fromtimestamp(cookie_cache["expiry"], timezone.utc):
                    rotate_code = cookie_cache["rotate_code"]
                    self._rotate_code_is_new = False
                self._next_rotation = datetime.fromtimestamp(cookie_cache["next_rotation"], timezone.utc)

        if not rotate_code:
            r = self._session.get(
                ROTATE_COOKIES_PAGE,
                headers={
                    "Referer": 'https://docs.google.com/',
                    "User-Agent": USER_AGENT
                })

            rotate_code = re.search(r"init\(\'([\d\-]+)\',", r.text)
            if not rotate_code:
                raise ValueError(CODE_ERROR)

            with open("cookie_cache.yml", "w") as cc_file:
                expiry = datetime.now(timezone.utc) + timedelta(days=1)
                rotate_code = rotate_code.group(1)
                yaml.dump({
                    "rotate_code": rotate_code,
                    "expiry": int(expiry.timestamp()),
                }, cc_file)

            self._rotate_code_is_new = True

        if self._rotate_code_is_new or self._needs_rotating():
            json_data = [None, rotate_code, 1]
            r = self._session.post(
                "https://accounts.google.com/RotateCookies",
                headers={
                    "Referer": ROTATE_COOKIES_PAGE,
                    "User-Agent": USER_AGENT
                }, json=json_data)

            if r.ok and (set_cookie := r.headers.get("Set-Cookie")):
                sidts = set_cookie.split("=")[1].split(";")[0]
            else:
                raise ValueError(CODE_ERROR)

            self._session.cookies.set("__Secure-1PSIDTS", sidts)
            self._next_rotation = datetime.now(timezone.utc) + timedelta(minutes=10)

            with open("credentials.yml", "r+") as creds_file:
                creds_data = yaml.safe_load(creds_file)
                creds_data["sidts"] = sidts
                creds_file.seek(0)
                yaml.dump(creds_data, creds_file)

            with open("cookie_cache.yml", "r+") as cc_file:
                cookie_cache = yaml.safe_load(cc_file)
                cookie_cache["next_rotation"] = int(self._next_rotation.timestamp())
                cc_file.seek(0)
                yaml.dump(cookie_cache, cc_file)
