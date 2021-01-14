import json
import requests
import urllib
import sys
import omeka_interfacer as O
import zotero_interfacer as Z
import re
from bs4 import BeautifulSoup
import datetime


zotero_items=Z.zotero_get_group_items(get_all=False)
zotero_item_ids=[item['key'] for item in zotero_items]
zotero_items_formatted=Z.zotero_format_items(zotero_items)

#now compare
#z_item_dict={i['zotero_id']:i for i in zotero_items_formatted}

property_map={
'title':['dcterms:title','literal'],
'abstract':['bibo:abstract','literal'],
'zotero_id':['bibo:identifier','literal'],
'url':['bibo:uri','uri'],
'date':['dcterms:date',"numeric:timestamp"],
'authors':['bibo:authorList','literal'],
'citation':['dcterms:bibliographicCitation','literal'],
'parentItem':['dcterms:isPartOf','resource'],
'childItem':['dcterms:hasPart','resource'],
'note':['acm5air:note','literal']
}

class_map={
'note':'bibo:Note',
'book':'bibo:ReferenceSource',
'attachment':'bibo:ReferenceSource',
'webpage':'bibo:ReferenceSource',
'journalArticle':'bibo:ReferenceSource'
}


omeka_class_term='bibo:Note'
omeka_zotero_id_property_term='bibo:identifier'
parentOf_property_term='dcterms:hasPart'
childOf_property_term='dcterms:isPartOf'


id_map={}
for item in zotero_items_formatted:
	print(item)
	item_type=item['item_type']
	item_class=class_map[item_type]
	item_properties=[]
	meta_properties=['modified','item_type','parentItem','downloadlink']
	zotero_id=item['zotero_id']
	for prop in item:
		if prop not in meta_properties:
			prop_term,prop_type=property_map[prop]
			if type(item[prop])==list:
				this_prop=[]
				for p in item[prop]:
					
					this_prop.append({
							'term':prop_term,
							'type':prop_type,
							'value':p
						})
				item_properties.append(this_prop)
			else:
				item_properties.append([{
						'term':prop_term,
						'type':prop_type,
						'value':item[prop]
					}])
	
	omeka_id=O.create_item(item_properties,item_class)
	id_map[zotero_id]=omeka_id
	
#now create links
'''for item in zotero_items_formatted:
	
	if 'parentItem' in item.keys():
		
		try:
			parent_omeka_id=id_map[item['parentItem']]
			self_omeka_id=id_map[item['zotero_id']]
		
			prop_term,prop_type=property_map['parentItem']
		
			child_properties=[{'term':prop_term,'type':prop_type,'value':parent_omeka_id}]
			print(child_properties)
		except:
			pass
		O.update_item(child_properties,self_omeka_id)
		
		term,type=property_map['childItem']
		
		parent_properties=[{'term':term,'type':type,'value':self_omeka_id}]
		
		O.update_item(parent_properties,parent_omeka_id)'''
		
		
	
	













