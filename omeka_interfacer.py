import json
import requests
import urllib
import sys

d = open('omeka_credentials.json','r')
t = d.read()
d.close()

omeka_credentials = json.loads(t)

'''omeka_credentials = {
    'key_identity': j['key_identity'],
    'key_credential': j['key_credential'],
    'base_url':j['base_url']
}'''

base_url=omeka_credentials['base_url']
base_path=omeka_credentials['base_path']

del(omeka_credentials['base_path'])
del(omeka_credentials['base_url'])

#basic urllib constructor
def build_url(this_base_url, path='', args_dict={}):
	url_parts = list(urllib.parse.urlparse(this_base_url))
	url_parts[2] = base_path+path
	url_parts[4] = urllib.parse.urlencode(args_dict)
	return urllib.parse.urlunparse(url_parts)


#path is like '/omeka/api/resource_classes'
#args_dict is like:
## {term:'bibo:Note'}  OR, if coming from advanced search
## {'property[0][property]': 98, 'property[0][type]': 'ex', 'property[0][joiner]': 'and'}
## optional get_all parameter, if set to True, will fetch all results using Omeka API pagination functionality
def omeka_get(path,args_dict,get_all=False):
	page=1
	
	all_results=[]
	
	while True:
		args_dict['page']=page
		this_url=build_url(base_url,path,args_dict)
		#print(this_url)
		response=requests.get(this_url,params=omeka_credentials)
		headers=response.headers
		j= json.loads(response.text)
		if len(j)>0:
			all_results += j
			page+=1
		else:
			break
		
		if get_all==False:
			break
	
	return all_results

#retrieves json object for omeka classes,properties,or templates based on search parameters
#accepts basic key/value params on these native resources, e.g. ('resource_classes',{'term':'bibo:Note'})
#super simple but a little inflexible
#right now my searches are only working with equivalencies between key/value pairs
def basic_search(resource_type,args_dict,get_all=True):
	j=omeka_get(resource_type,args_dict,get_all)
	return j


#advanced search args allow for some clever filters
#Right now it's super helpful for only grabbing items that have a specific property, which keeps me from having to iterate over all items looking for a value there
#e.g. advanced_args=[{'property_id':98,'operator':'ex'}]
def advanced_search(resource_type=None,args_dict={},advanced_args=[],get_all=True):
	
	p=0
	
	for arg in advanced_args:
		args_dict['property[%d][property]' %p]=arg['property_id']
	
		args_dict['property[%d][type]' %p]=arg['operator']
	
		#"ex" -- which is to say, "exists" does not require a value
		if arg['operator']!='ex':
			args_dict['property[%d][text]' %p]=arg['value']
	
		#for now, gonna hard-code in an "and" joiner between arguments
		args_dict['property[%d][joiner]' %p]='and'
		p+=1
	
	#print(args_dict)
	j=omeka_get(resource_type,args_dict,get_all)
	
	return j
	

def create_item(properties,item_class=''):
	
	#print(properties)
	
	properties_dump={}
	for p in properties:
		term=p[0]['term']
		property_id=basic_search('properties',{'term':term})[0]['o:id']
		
		if type(p)==list:
			prop_data=[]
			for prop_entry in p:
				prop_data.append({
					"type": prop_entry['type'],
					"property_id":property_id,
					"@value":prop_entry['value']
					})
		else:
			prop_data=[{
				"type": p['type'],
				"property_id":property_id,
				"@value":p['value']
				}]
		
		properties_dump[term]=prop_data

	resource_class_id=basic_search('resource_classes',{'term':item_class})[0]['o:id']
	
	data = {
	
	
	"@type": ["o:Item",item_class],
	
	"o:resource_class": 
			{
				"o:id": resource_class_id,
				"@id": build_url(base_url,'resource_classes/%d' %resource_class_id)
			}
	}
	
	for p in properties_dump:
		data[p]=properties_dump[p]
	
	print(data)
	
	headers = {
	'Content-type': 'application/json'
	}
	url=build_url(base_url,'items')
	print(json.dumps(data))
	response = requests.post(url, params=omeka_credentials, data=json.dumps(data), headers=headers)
	#print(response.text)
	j = json.loads(response.text)
	
	#print(j)
	
	#print(j['o:id'])
	return j['o:id']