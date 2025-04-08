import json
from entry import Entry, EntryDict, set_default
from glob import glob

def is_match(entry: Entry, other: Entry):
    if entry.type == "pulled" or other.type == "pulled":
        return False
    if other.revision < entry.revision:
        return False
    if (entry.type == "accidental" and other.type == "official (reairing)") or \
       (entry.type == "official (reairing)" and other.type == "accidental"):
        return False
    if entry.episode == other.episode and entry.revision != other.revision:
        return True
    if entry.episode.isdigit() and other.episode.startswith(entry.episode) and len(other.episode) > len(entry.episode) and not other.episode[len(entry.episode)].isdigit():
        return True

for json_path in glob("*.json"):
    with open(json_path, "r+") as json_file:
        entries_dict = EntryDict(json.load(json_file))
        for channel, entries in entries_dict.items():
            for entry in entries:
                matches = [e2 for e2 in entries if is_match(entry, e2)]
                matches.sort(key=lambda match: match.revision, reverse=True)

                if matches:
                    entry.type = "pulled"
                    episodes = set()
                    for match in matches:
                        if match.episode in episodes:
                            match.type = "pulled"
                        else:
                            episodes.add(match.episode)

        json_file.seek(0)
        json.dump(entries_dict, json_file, indent=4, default=set_default)
