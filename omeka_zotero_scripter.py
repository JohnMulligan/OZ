import json
import requests
import urllib
import sys
import omeka_interfacer as O
import zotero_interfacer as Z

omeka_class_term='bibo:Note'
omeka_zotero_id_property_term='bibo:identifier'






omeka_class_id = O.basic_search('resource_classes',{'term':omeka_class_term},get_all=False)[0]['o:id']
omeka_zotero_id_property_id = O.basic_search('properties',{'term':omeka_zotero_id_property_term},get_all=False)[0]['o:id']

omeka_zotero_items=O.advanced_search(resource_type='items',advanced_args=[{'property_id':omeka_zotero_id_property_id,'operator':'ex'}],get_all=True)

print("found %d zotero items in omeka" %len(omeka_zotero_items))


zotero_items=Z.zotero_get_group_items(get_all=False)
zotero_item_ids=[item['key'] for item in zotero_items]
zotero_items_children=Z.zotero_get_children(zotero_item_ids)




