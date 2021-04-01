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



#first, fetch initial zotero items
zotero_items=Z.zotero_get_group_items(get_all=True)
zotero_item_ids=[item['key'] for item in zotero_items]
zotero_items_formatted=Z.zotero_format_items(zotero_items)


#then, establish hard-coded map of zotero properties and classes to omeka properties and classes
#would help to have some up-front validation of this
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
'note':['bibo:abstract','literal'],
'filename':['dcterms:title','literal']
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


#need this to fetch zotero attachment files
d = open('zotero_credentials.json','r')
t = d.read()
d.close()
j = json.loads(t)
zotero_credentials = {
    'key': j['Zotero-API-Key'],
    'group': j['group']
}



omeka_zotero_id_property_term_id=O.basic_search('properties',{'term':omeka_zotero_id_property_term},retrieve_all=False)[0]['o:id']


#helpfully mines zotero-style property trees
#and formats into omeka-style property trees
##note--these aren't request-ready json payloads. i do this in omeka_interfacer.format_property_data because omeka's namespace is ... idiosyncratic
def format_properties(item,ignore_properties=[]):
	item_properties=[]
	#zotero_id=item['zotero_id']
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

print("number of items with summaries:",len(zotero_items_formatted))

#consolidate non-attachment items
summaries={}
#first get all summaries
for item in zotero_items_formatted:
	item_type=item['item_type']
	#ignore attachment items
	if item_type!='attachment' and 'title' in item and re.fullmatch('summary',re.sub('[,|.|:|;|-|!|?]+','',item['title'].strip().lower())):
		z_id=item['zotero_id']
		note=item['note']
		parent_id=item['parentItem']
		modified=item['modified']		
		summaries[z_id]={'note':note,'parentItem':parent_id,'modified':modified}

#then purge them from the master list
zotero_items_formatted=[i for i in zotero_items_formatted if i['zotero_id'] not in summaries]

#then roll them into the master list via parent item abstracts
for s_id in summaries:
	s_text=summaries[s_id]['note']
	s_parent_id=summaries[s_id]['parentItem']
	z_parent=None
	for z_item in zotero_items_formatted:
		if s_parent_id==z_item['zotero_id']:
			z_parent=z_item
			#print(s_parent_id,s_id)
	if z_parent!=None:
		zotero_items_formatted.remove(z_parent)
		if 'note' in z_parent:
			z_parent['note'].append(s_text)
		else:
			z_parent['note']=[s_text]
		zotero_items_formatted.append(z_parent)
		
print("number of items after rolling up summaries",len(zotero_items_formatted))

# now get all Omeka items with bibo:identifier
omeka_media=O.basic_search('items',retrieve_all=True)
omeka_items=O.basic_search('media',retrieve_all=True)

d=open('otmp.json','w')
d.write(json.dumps(omeka_items))
d.close()

#odt=[{'zotero_id':o[omeka_zotero_id_property_term][0]['@value'],'omeka_id':o['o:id'],'modified':['o:modified']['@value']} for o in omeka_items if omeka_zotero_id_property_term in o]
OZ_dict={o[omeka_zotero_id_property_term][0]['@value']:o['o:id'] for o in omeka_items + omeka_media if omeka_zotero_id_property_term in o}
oz_items={o['o:id']:datetime.datetime.fromisoformat(o['o:modified']['@value']) for o in omeka_items + omeka_media}


print(zotero_items_formatted)

print(oz_items)

#create non-attachment items
c=1
d=1
for item in zotero_items_formatted:
	item_type=item['item_type']
	#ignore attachment items
	if item_type!='attachment':
		try:
			item_class=class_map[item_type]
		except:
			item_class=class_map['default_class']
		item_properties=format_properties(item,ignore_properties=['modified','item_type','parentItem','downloadlink'])
		zotero_id=item['zotero_id']
		if zotero_id in OZ_dict:
			omeka_id=OZ_dict[zotero_id]
			o_timestamp=oz_items[omeka_id]
			z_timestamp=item['modified']
			if o_timestamp < z_timestamp:
				O.update_item(item_properties,omeka_id,keep_links=True,keep_nonlinks=False)
				print('updated %d omeka_id=%d' %(d,omeka_id),"zotero id=",zotero_id)
				d+=1
			else:
				print("not updating",omeka_id,zotero_id,"--omeka is fresher")
		else:
			omeka_id=O.create_item(item_properties,item_class)
			print("created %d omeka_id=%d" %(c,omeka_id),"zotero id=",zotero_id)
			c+=1

#upload attachments or create new attachment items
attachment_items=[i for i in zotero_items_formatted if i['item_type']=='attachment']
for item in attachment_items:
	#all attachment items have properties we can look up, map, and format
	zotero_id=item['zotero_id']
	
	if zotero_id not in OZ_dict:
	
		item_properties=format_properties(item,ignore_properties=['modified','item_type','parentItem','downloadlink','linkmode'])
		#but some don't have parent items or have broken links to deleted parent items -- if so, create an item for the attachment
		if 'parentItem' in item.keys():
			print("\nattachment item",item['zotero_id'],"parent item",item['parentItem'])
			parent_item_zotero_id=item['parentItem']
			args_dict={'property_id':omeka_zotero_id_property_term_id,'operator':'eq','value':parent_item_zotero_id}
			try:
				parent_item_omeka_id=O.advanced_search('items',advanced_args=[args_dict],retrieve_all=False)[0]['o:id']
			except:
				print("^^ error -- parent item not found -- creating standalone item ^^\n")
				parent_item_omeka_id=O.create_item(item_properties,class_map['default_class'])
		else:
			parent_item_omeka_id=O.create_item(item_properties,class_map['default_class'])
	
		#next -- some so-called attachments are just links stored in a funky way.
		#what's worse, some attached files have broken links
		if item['linkmode']=='imported_file':
			try:
				dl=item['downloadlink']
				fname=item['filename']
				print("fetching file %s" %fname)
				response=requests.get(dl,params=zotero_credentials,allow_redirects=True)
				open(fname,'wb').write(response.content)
				O.upload_attachment(parent_item_omeka_id,item_properties,fname)
				os.remove(fname)
			except:
				print("^^ error -- download file not available ^^\n",item,'\n')
				item_properties=format_properties({'url':item['url']})
				omeka_id=O.update_item(item_properties,parent_item_omeka_id)	
		else:
			item_properties=format_properties({'url':item['url']})
			omeka_id=O.update_item(item_properties,parent_item_omeka_id)
	else:
		print("item already uploaded. skipping:",zotero_id)

#now create links between all items
for item in zotero_items_formatted:
	
	if 'parentItem' in item.keys():
		try:
			advanced_args=[{'property_id':omeka_zotero_id_property_term_id,'operator':'eq','value':item['parentItem']}]
			#print(advanced_args)
			parent_omeka_id=O.advanced_search('items',advanced_args=advanced_args)[0]['o:id']
			advanced_args=[{'property_id':omeka_zotero_id_property_term_id,'operator':'eq','value':item['zotero_id']}]
			#print(advanced_args)
			self_omeka_item=O.advanced_search('items',advanced_args=advanced_args)
			self_omeka_id=self_omeka_item[0]['o:id']
			print(self_omeka_item)
			#get all links:
			links=[]
			for p in self_omeka_item[0]:
				if type(self_omeka_item[0][p])==list:
					for si in self_omeka_item[0][p]:
						try:
							if si['type']=='resource':
								links.append(si['value_resource_id'])
						except:
							pass
			#print(links)
			
			if item['parentItem'] not in links:
				print('linking',item['parentItem'],parent_omeka_id,'to',item['zotero_id'],self_omeka_id)
				skipthis=False
			else:
				print('link already exists:',item['parentItem'],parent_omeka_id,'to',item['zotero_id'],self_omeka_id)
				skipthis=True
		except:
			print("one of these does not exist in omeka:",item['parentItem'],item['zotero_id'])
			skipthis=True
		
		if skipthis!=True:
			
			prop_term,prop_type=property_map['parentItem']
			child_properties=[{'term':prop_term,'type':prop_type,'value':parent_omeka_id}]
			O.update_item(child_properties,self_omeka_id)
			prop_term,prop_type=property_map['childItem']
			parent_properties=[{'term':prop_term,'type':prop_type,'value':self_omeka_id}]
			O.update_item(parent_properties,parent_omeka_id)
		
