import json
import os
import re
import sys
from datetime import datetime
from session import DocsSession
from yarl import URL

doc_id = sys.argv[1] if len(sys.argv) > 1 else input("Document ID: ")
user_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0

session = DocsSession(user_id)
session.load_doc(doc_id)
info_token = session.get_info_token()
sid = session.get_session_id()

def save_revision(start, end, ts, gid=0):
    r = session.get(f"/revisions/show?sid={sid}&token={info_token}&includes_info_params=true&cros_files=false&rev={end}&fromRev={start}&gid={gid}")
    if not r.ok:
        raise RuntimeError(f"Show request failed: {r.text} {r.status_code}")

    sheet_prefix = ""
    if sheet_name_regex := re.search(r"<title>(.*?)<\/title>", r.text):
        sheet_prefix = sheet_name_regex.group(1) + "/"

    if gid == 0:
        if sheet_data_regex := re.search(r"parent.__registerSheetNames\((.*?),  0.0", r.text):
            sheets = json.loads(sheet_data_regex.group(1))
            for sheet in sheets:
                if sheet["changed"] and sheet["id"] != gid:
                    save_revision(start, end, ts, sheet["id"])

    if "changed\" " in r.text: # any changes SHOULD be reflected in elements with "changed" at the end of their class name, so this check should always hit if there are any. the space is to not hit the "changed" values in the sheet data above
        file_path = f"out/{sheet_prefix}{datetime.fromtimestamp(ts).isoformat()}.html"
        print(f"Saving {file_path}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as html_file:
            html_file.write(r.text)

endpoint = URL(f"/revisions/tiles?id={doc_id}&start=1&revisionBatchSize=1500&showDetailedRevisions=false&loadType=0&token={info_token}&includes_info_params=true&cros_files=false")
first_rev = -1

while first_rev != 1:
    r = session.get(endpoint)
    if not r.ok:
        raise RuntimeError(f"Tiles request failed: {r.text} {r.status_code}")

    tiles = json.loads(r.text[5:])
    for tile in reversed(tiles["tileInfo"]):
        save_revision(tile["start"], tile["end"], tile["endMillis"] / 1000)

    first_rev = tiles["firstRev"]
    endpoint = endpoint.update_query(end=first_rev)
