import dominate
import functools
import json
import os
from datetime import datetime
from dominate.tags import *
from glob import glob
from sortedcontainers import SortedList

class HistoricalEntry:
    def __init__(self, prefix, data):
        self.prefix = prefix
        self.episode = data["episode"]
        self.time = datetime.fromisoformat(data["time"])
        match data["type"]:
            case "leak": self.color = "#0000ff"
            case "pulled": self.color = "#ff0000"
            case "accidental": self.color = "#00ff00"
            case "official (reairing)": self.color = "#ff9900"
            case _: self.color = ""

    def compare_desc(self, other):
        if self.time < other.time:
            return 1
        elif self.time > other.time:
            return -1
        else:
            return 0

    def time_str(self):
        return self.time.strftime("%Y-%m-%d @ %-I:%M %p")

def entry_list():
    return SortedList(key=functools.cmp_to_key(HistoricalEntry.compare_desc))

channel_entries = {
    "Nickelodeon Arabia": entry_list(),
    "Nickelodeon Asia": entry_list(),
    "Nickelodeon Australia": entry_list(),
    "Nickelodeon Austria and Switzerland": entry_list(),
    "Nickelodeon Brazil": entry_list(),
    "Nickelodeon Canada": entry_list(),
    "Nickelodeon Central/South America": entry_list(),
    "Nickelodeon Commercial Alt": entry_list(),
    "Nickelodeon Commercial Light": entry_list(),
    "Nickelodeon France": entry_list(),
    "Nickelodeon Germany": entry_list(),
    "Nickelodeon Global": entry_list(),
    "Nickelodeon Global Commercial": entry_list(),
    "Nickelodeon Italy": entry_list(),
    "Nickelodeon Mexico": entry_list(),
    "Nickelodeon Netherlands": entry_list(),
    "Nickelodeon Poland": entry_list(),
    "Nickelodeon Russia": entry_list(),
    "Nickelodeon South Africa": entry_list(),
    "Nickelodeon Southeast Asia": entry_list(),
    "Nickelodeon UK": entry_list(),
    "Nickelodeon USA": entry_list(),
    "Nickelodeon Ukraine": entry_list(),
    "Nicktoons Global": entry_list(),
    "Nicktoons Global Commercial": entry_list(),
    "Nicktoons South Africa": entry_list(),
    "Nicktoons UK": entry_list(),
    "Nicktoons USA": entry_list(),
    "TeenNick USA": entry_list(),
    "YTV": entry_list()
}

for json_path in glob("*.json"):
    json_name = os.path.splitext(os.path.basename(json_path))[0]
    prefix = {
        "Kamp Koral": "KMPK",
        "Rock Paper Scissors": "RPS",
        "SpongeBob SquarePants": "XSP",
        "The Casagrandes": "CASA",
        "The Loud House": "LDH",
        "The Patrick Star Show": "PATS"
    }.get(json_name, "")
    with open(json_path, "r") as json_file:
        data = json.load(json_file)
        for channel, entries in data.items():
            for entry in entries:
                channel_entries[channel].add(HistoricalEntry(prefix, entry))

doc = dominate.document()

with doc:
    with table():
        with tbody():
            with tr():
                with td():
                    span("color key:")
                    span("leak").set_attribute("style", "color:#0000ff")
                    span("pulled").set_attribute("style", "color:#ff0000")
                    span("accidental").set_attribute("style", "color:#00ff00")
                    span("official (reairing)").set_attribute("style", "color:#ff9900")
                for channel in channel_entries.keys():
                    td(channel)
            while any(queue for queue in channel_entries.values()):
                with tr():
                    td() # need an empty one
                    for list in channel_entries.values():
                        if not list:
                            td()
                            continue
                        entry: HistoricalEntry = list.pop(0)
                        with td(f"{entry.prefix} {entry.episode} ({entry.time_str()})"):
                            if entry.color:
                                attr(style=f"color:{entry.color}")

with open("doc.html", "w") as doc_file:
    doc_file.write(doc.render())