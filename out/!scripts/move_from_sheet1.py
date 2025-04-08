import json
import os
from entry import Entry, EntryDict, set_default

with open("Kamp Koral.json", "r") as kk_file:
    kk_entries = EntryDict(json.load(kk_file))
with open("SpongeBob SquarePants.json", "r") as sb_file:
    sb_entries = EntryDict(json.load(sb_file))
with open("The Patrick Star Show.json", "r") as pss_file:
    pss_entries = EntryDict(json.load(pss_file))

with open("Sheet1.json") as sheet1_file:
    sheet1_data = json.load(sheet1_file)
    for channel, entries in sheet1_data.items():
        for entry in entries:
            episode = entry["episode"]
            if episode.startswith("KK"):
                entry["episode"] = episode[2:]
                kk_entries.add(channel, Entry.fromdata(entry))
            elif episode.startswith("PSS"):
                entry["episode"] = episode[3:]
                pss_entries.add(channel, Entry.fromdata(entry))
            else:
                sb_entries.add(channel, Entry.fromdata(entry))

with open("Kamp Koral.json", "w") as kk_file:
    json.dump(kk_entries, kk_file, indent=4, default=set_default)
with open("SpongeBob SquarePants.json", "w") as sb_file:
    json.dump(sb_entries, sb_file, indent=4, default=set_default)
with open("The Patrick Star Show.json", "w") as pss_file:
    json.dump(pss_entries, pss_file, indent=4, default=set_default)
os.remove("Sheet1.json")
