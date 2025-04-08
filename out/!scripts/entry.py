import functools
from datetime import datetime, timezone
from sortedcontainers import SortedSet
from typing import override

EDGE_CASES = {
    "2021-12-22 @ 16;55": "2021-12-22 @ 16:55",
    "2022-02-20 7:40": "2022-02-20 @ 7:40",
    "2022-11-07 @ 17:00)": "2022-11-07 @ 17:00",
    "2022-12-04 @19:40": "2022-12-04 @ 19:40",
    "2024-09-19 @ 4:00 P": "2024-09-19 @ 4:00 PM"
}

class Entry:
    def __init__(self, text, _type, revision):
        paren_idx = text.find("(")
        time_str = text[(paren_idx + 1):-1]
        if time_str in EDGE_CASES:
            time_str = EDGE_CASES[time_str]

        self.episode = text[:(paren_idx - 1)]
        self.revision = revision
        self.type = _type

        try:
            if time_str.endswith("AM") or time_str.endswith("PM"):
                self.time = utcptime(time_str, "%Y-%m-%d @ %I:%M %p").isoformat()
            else:
                self.time = utcptime(time_str, "%Y-%m-%d @ %H:%M").isoformat()
        except ValueError as e:
            print(f"Attempt to resolve time for entry ({self.episode} @ {time_str}) failed. {e}")
            self.time = ""

    def compare_desc(self, other):
        if self.time < other.time:
            return 1
        elif self.time > other.time:
            return -1
        else:
            return 0

    @classmethod
    def fromdata(cls, data: dict):
        inst = cls.__new__(cls)
        for key, value in data.items():
            if key == "time":
                inst.time = datetime.fromisoformat(value)
            else:
                inst.__dict__[key] = value
        return inst

    @override
    def __repr__(self):
        return f"<Entry episode:{self.episode} time:{self.time} type:{self.type} revision:{self.revision}>"

    @override
    def __str__(self):
        return f"{self.episode} ({self.time}) ({self.type}) from {self.revision}"

    @override
    def __eq__(self, other):
        if isinstance(other, Entry):
            return self.episode == other.episode and self.time == other.time
        return False

    @override
    def __hash__(self):
        return hash(self.episode) ^ hash(self.time)

    def __lt__(self, other):
        if isinstance(other, Entry):
            return self.time < other.time
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Entry):
            return self.time > other.time
        return NotImplemented

class EntryDict(dict):
    def __init__(self, data: dict):
        dict.__init__(self)
        for channel, entries in data.items():
            self[channel] = SortedSet(
                [Entry.fromdata(e) for e in entries],
                functools.cmp_to_key(Entry.compare_desc))

    def add(self, channel: str, entry: Entry):
        if channel not in self:
            self[channel] = SortedSet(key=functools.cmp_to_key(Entry.compare_desc))
        self[channel].add(entry)

def set_default(obj):
    if isinstance(obj, SortedSet):
        return list(obj)
    elif isinstance(obj, Entry):
        return obj.__dict__
    elif isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError

def utcptime(date_string: str, format: str):
    return datetime.strptime(date_string, format).replace(tzinfo = timezone.utc)
