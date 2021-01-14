import json
import requests
import urllib
import sys
import omeka_interfacer as O
import zotero_interfacer as Z
import re
from bs4 import BeautifulSoup
import datetime


#zotero returns timestamps in the format "2019-08-14T15:04:07Z"
#omeka returns them in the format "2021-01-13T20:18:37+00:00"
#and right now, my omeka and zotero api's are on the same clock, so i'm going to ignore the timezone question
def datetime_reducer(dt):
	formatted_date=datetime.datetime.strptime(re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}",dt).group(0),'%Y-%m-%dT%H:%M:%S')
	return(formatted_date)
	
omeka_class_term='bibo:Note'
omeka_zotero_id_property_term='bibo:identifier'
parentOf_property_term='dcterms:hasPart'
childOf_property_term='dcterms:isPartOf'


#get omeka items that:
#A) are of class "omeka_class_term"
#B) have a value for property "omeka_zotero_id_property_term"

omeka_class_id = O.basic_search('resource_classes',{'term':omeka_class_term},get_all=False)[0]['o:id']
omeka_zotero_id_property_id = O.basic_search('properties',{'term':omeka_zotero_id_property_term},get_all=False)[0]['o:id']
omeka_zotero_items=O.advanced_search(resource_type='items',advanced_args=[{'property_id':omeka_zotero_id_property_id,'operator':'ex'}],get_all=True)

#now reduce these items to some basic data we need for comparing with the zotero Library
omeka_zotero_items_formatted=[]
for i in omeka_zotero_items:
	item={}
	item['zotero_id']=i[omeka_zotero_id_property_term][0]['@value']
	item['modified']=datetime_reducer(i['o:modified']['@value'])
	item['omeka_id']=i['o:id']
	item['resource_class_id']=i['o:resource_class']['o:id']
	omeka_zotero_items_formatted.append(item)

for item in omeka_zotero_items_formatted:
	print(item['zotero_id'],item['modified'],item['resource_class_id'])

print("found %d zotero items in omeka" %len(omeka_zotero_items))


zotero_items=Z.zotero_get_group_items(get_all=False)
zotero_item_ids=[item['key'] for item in zotero_items]
#print(zotero_item_ids)
#don't need this -- child items are included in the get all items function
#zotero_items_children=Z.zotero_get_children(zotero_item_ids)


zotero_items_formatted=Z.zotero_format_items(zotero_items)

#now compare
z_item_dict={i['zotero_id']:i for i in zotero_items_formatted}
o_item_dict={i['zotero_id']:i for i in omeka_zotero_items_formatted}




for item in zotero_items_formatted:
	modified=datetime_reducer(item['modified'])
	zotero_id=item['zotero_id']
	item_type=item['item_type']
	print(zotero_id,modified,item_type)


	


'title'
'abstract'
'zotero_id'
'url'
'date'
'authors'