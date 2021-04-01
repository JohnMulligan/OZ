import json
import requests
import urllib
import sys
import omeka_interfacer as O
import zotero_interfacer as Z
import re
from bs4 import BeautifulSoup
import datetime
import os
from datetime import datetime


# This one tells you which items are newer where.
# However, the timestamps look off, empirically.
# Don't quite trust this yet, so I'm going to 

zotero_items=Z.zotero_get_group_items(get_all=True)
zotero_item_ids=[item['key'] for item in zotero_items]
zotero_items_formatted=Z.zotero_format_items(zotero_items)

zdt={z['key']:z['data']['dateModified'] for z in zotero_items}

omeka_items=O.basic_search('items',retrieve_all=True)

odt={o['bibo:identifier'][0]['@value']:o['o:modified']['@value'] for o in omeka_items if 'bibo:identifier' in o}

omeka_z_keys=set(odt.keys())
zotero_z_keys=set(zdt.keys())

zotero_only=zotero_z_keys-omeka_z_keys
print("items only in zotero:",zotero_only)

print("-------------------")
omeka_only=omeka_z_keys-zotero_z_keys
print("items only in omeka:",omeka_only)

combined={i:[datetime.fromisoformat(zdt[i][:-1]+'+00:00'),datetime.fromisoformat(odt[i])] for i in omeka_z_keys & zotero_z_keys}

print("-------------------")

print("timestamp diff -- positive if omeka is newer")

for c in combined:
	print(c,combined[c][0]-combined[c][1])