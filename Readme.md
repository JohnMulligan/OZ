# Omeka-S / Zotero Group Library sync

This will import items from Zotero into Omeka.

It tracks items with Zotero unique ID's.

It will maintain linking between child items (e.g., notes) and parent items (e.g., sources).

The first iteration won't deal with complex metadata beyond the item linking.

Ideally, it will also be more than a one-way importer, and will check against id's and timestamps in oder to prompt the user for updates from zotero based on more recent changes. This seems doable.

The Omeka interfacer python file already has a good start at using the Omeka-S advanced search API.



https://www.zotero.org/support/dev/web_api/v3/start

https://omeka.org/s/docs/developer/api/rest_api/