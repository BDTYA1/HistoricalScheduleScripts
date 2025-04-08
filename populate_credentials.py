import sys
import yaml

if len(sys.argv) <= 1:
    raise ValueError("Need to provide cookie string as argument")

NAME_MAP = {
    "SID": "sid",
    "HSID": "hsid",
    "SSID": "ssid",
    "APISID": "apisid",
    "SAPISID": "sapisid",
    "OSID": "osid",
    "__Secure-1PSIDTS": "sidts"
}

data = {}

cookies = sys.argv[1].split("; ")
for cookie in cookies:
    if (eq_ind := cookie.find("=")) != -1 and len(cookie) > eq_ind:
        name = cookie[:eq_ind]
        if name in NAME_MAP:
            data[NAME_MAP[name]] = cookie[(eq_ind + 1):]

with open("credentials.yml", "w") as creds_file:
    yaml.dump(data, creds_file)
