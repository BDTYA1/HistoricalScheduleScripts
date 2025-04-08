import functools
import itertools
import json
import more_itertools
import os
from bs4 import BeautifulSoup
from cssutils import CSSParser
from entry import Entry, set_default
from glob import glob
from sortedcontainers import SortedSet

CHANNELS = [
    ["Nicktoons Global Commercial", "NickToons Netherlands", "NickToons Germany", "NickToons Commercial (Poland)", "NickToons Commercial", "NickToons Global Commercial", "NickToons Poland"],
    ["Nickelodeon Italy"],
    ["TeenNick USA"],
    ["Nickelodeon Mexico", "Nickelodeon Latin America (Mexico)"],
    ["Nickelodeon Asia", "Nickelodeon Global Unlimited"],
    ["Nickelodeon Southeast Asia"],
    ["Nickelodeon Central/South America", "Nickelodeon Latin America (Central)"],
    ["Nicktoons South Africa", "NickToons South Africa", "NickToons Africa"],
    ["Nickelodeon Germany"],
    ["Nickelodeon Austria and Switzerland", "Nickelodeon Austria", "Nickelodeon Switzerland"],
    ["Nicktoons UK", "NickToons UK"],
    ["Nickelodeon Commercial Alt", "Nickelodeon South Africa and Scandinavia"],
    ["Nickelodeon Global", "Nickelodeon Global Opt-Out"],
    ["Nickelodeon USA"],
    ["Nickelodeon Commercial Light", "Nickelodeon Iberia", "Nickelodeon Wallonia"],
    ["Nickelodeon Canada"],
    ["Nickelodeon Netherlands", "Nickelodeon Belgium", "Nickelodeon Flanders"],
    ["Nickelodeon South Africa", "Nickelodeon Africa", "Nickelodeon Turkey"],
    ["Nickelodeon UK"],
    ["Nickelodeon Global Commercial"],
    ["YTV"],
    ["Nickelodeon Russia"],
    ["Nickelodeon France"],
    ["Nickelodeon Australia"],
    ["Nickelodeon Poland"],
    ["Nickelodeon Arabia", "Nickelodeon Middle East", "Nickelodeon MENA"],
    ["Nicktoons USA"],
    ["Nickelodeon Brazil"],
    ["Nickelodeon Ukraine"],
    ["Nicktoons Global", "NickToons Global"]
]

COLOR_MAP = {
    "#00f": "leak",
    "#f00": "unconfirmed",
    "#0f0": "accidental",
    "#f90": "official (reairing)"
}

css_parser = CSSParser()

for item in os.listdir("../"):
    item_path = os.path.abspath(os.path.join("..", item))
    if not os.path.isdir(item_path):
        continue

    json_obj = dict()
    title = None

    for html_path in glob(os.path.join(item_path, "*.html")):
        html_name = os.path.splitext(os.path.basename(html_path))[0]
        with open(html_path) as html_file:
            soup = BeautifulSoup(html_file, features="lxml")
            stylesheets = [css_parser.parseString(s.string or "") for s in soup.select("style")]
            rows = soup.select("tbody tr")

            if not title and soup.title:
                title = soup.title.string

            for row in itertools.islice(rows, 2, None):
                channel = more_itertools.nth(row.children, 1)
                if not channel or not (match := next((c for c in CHANNELS if channel.text in c), None)):
                    continue

                for child in itertools.islice(row.children, 3, None):
                    if not child.text or child.text.isspace():
                        continue

                    child_class = "." + child["class"][0]
                    color = next((
                        rule.style.getPropertyValue("color")
                        for stylesheet in stylesheets
                        for rule in stylesheet
                        if child_class in rule.selectorText
                    ), "")

                    if match[0] not in json_obj:
                        json_obj[match[0]] = SortedSet(key=functools.cmp_to_key(Entry.compare_desc))

                    entry = Entry(child.text, COLOR_MAP.get(color, "normal"), html_name)
                    if entry.time and entry.type != "unconfirmed":
                        json_obj[match[0]].add(entry)

    if title:
        with open(f"{title}.json", "w") as json_file:
            json.dump(json_obj, json_file, indent=4, default=set_default)
