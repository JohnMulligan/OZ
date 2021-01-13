import json
import requests
import urllib

d = open('zotero_credentials.json','r')
t = d.read()
d.close()

j = json.loads(t)

zotero_credentials = {
    'key': j['Zotero-API-Key'],
    'group': j['group']
}
group_id=zotero_credentials['group']
base_url='https://api.zotero.org/'

def build_url(this_base_url, path,args_dict):
	url_parts = list(urllib.parse.urlparse(this_base_url))
	url_parts[2] = path
	url_parts[4] = urllib.parse.urlencode(args_dict)
	return urllib.parse.urlunparse(url_parts)

#path is like '/groups/12345/items'
#start parameter allows for pagination
def zotero_get_group_items(get_all=False):
	
	params=zotero_credentials
	args_dict={}
	start=0
	all_results=[]
	while True:
		args_dict['start']=start
		this_url=build_url(base_url,'/groups/'+str(group_id)+'/items/',args_dict)
		print(this_url)
		response=requests.get(this_url,params=params)
		headers=response.headers
		j=json.loads(response.text)
		for i in j:
			print(i['key'])
		if len(j)>0:
			all_results += j
			start+=len(j)
		else:
			break
		
		if get_all==False:
			break
	
	return all_results
	
def zotero_get_children(item_ids):
	
	children={id:[] for id in item_ids}
	params=zotero_credentials
	args_dict={}
	for id in item_ids:
		#"start" is the zotero api's offset parameter
		start=0
		while True:
			args_dict['start']=start
			this_url=build_url(base_url,'/groups/'+str(group_id)+'/items/'+str(id)+'/children',args_dict)
			print(this_url)
			response=requests.get(this_url,params=params)
			headers=response.headers
			try:
				j=json.loads(response.text)
			
				for i in j:
					print(i['key'])
				if len(j)>0:
					children[id] += j
					start+=len(j)
				else:
					break
			except:
				print(response)
				break
	return children