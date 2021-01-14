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
'note':['acm5air:note','literal'],
'filename':['o:source','literal']
}

class_map={
'note':'bibo:Note',
'book':'bibo:ReferenceSource',
'attachment':'bibo:ReferenceSource',
'webpage':'bibo:ReferenceSource',
'journalArticle':'bibo:ReferenceSource',
'default_class':'bibo:ReferenceSource'
}


omeka_class_term='bibo:Note'
omeka_zotero_id_property_term='bibo:identifier'
parentOf_property_term='dcterms:hasPart'
childOf_property_term='dcterms:isPartOf'

omeka_zotero_id_property_term_id=O.basic_search('properties',{'term':omeka_zotero_id_property_term})[0]['o:id']



#i screen out the below properties when pushing to omeka, typically
meta_properties=['modified','item_type','parentItem','downloadlink']








def format_properties(item,ignore_properties=[]):
	item_properties=[]
	zotero_id=item['zotero_id']
	for prop in item:
		if prop not in ignore_properties:
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
	return(item_properties)

id_map={}
c=0

#upload normal items, while fetching along the way:
##omeka id's mapped to zotero id's
##attachment items being shunted off into a separate list


'''for item in zotero_items_formatted:
	
	item_type=item['item_type']
	
	if item_type!='attachment':
		try:
			item_class=class_map[item_type]
		except:
			item_class=class_map['default_class']
		item_properties=format_zotero_properties_for_omeka'''
		
		'''
		item_properties=[]
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
						}])'''
		'''omeka_id=O.create_item(item_properties,item_class)
		id_map[zotero_id]=omeka_id
		c+=1
		print("created %d omeka_id=%d zotero_id=%d" %(c,omeka_id,zotero_id))'''

#handle attachment items
attachment_items=[i for i in zotero_items_formatted if i['item_type']=='attachment']

for item in attachment_items:
	
	if 'parentItem' in item.keys():
		parent_item_zotero_id=item['parentItem']
		print(parent_item_zotero_id)
		args_dict={'property_id':omeka_zotero_id_property_term_id,'operator':'eq','value':parent_item_zotero_id}
		print(args_dict)
		parent_item_data=O.advanced_search('items',advanced_args=[args_dict],retrieve_all=False)[0]
		parent_item_omeka_id=parent_item_data['o:id']
		
		print(formatted_properties)
		##if we don't have a downloadable attachment file (zotero has "url attachments" and other weird shit), then make a new item with the data we do have
		if 'downloadlink' not in item.keys():
			formatted_properties=format_properties(item,ignore_properties=['modified','item_type','parentItem'])
			omeka_id=O.create_item(formatted_properties,class_map['default_class'])
			id_map[zotero_id]=omeka_id
		else:
			formatted_properties==format_properties(item,ignore_properties=['modified','item_type','parentItem'])
			fname=item['filename']
			print("fetching file %s" %fname)
			response=requests.get(item['downloadlink'],allow_redirects=True)
			open(fname,'wb').write(response.content)
			O.upload_attachment(parent_item_omeka_id,fname)
			os.remove(fname)
			
			
			
	'''except:
		print(item['zotero_id'],"has no parent. creating standalone item.")'''
		
	#print("parent item",parent_item_data)
	
	
	#print(parent_item_zotero_id,item)
	
	#omeka_id=O.upload_attachment()



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
		
		O.update_item(parent_properties,parent_omeka_id)
		
		
	'''