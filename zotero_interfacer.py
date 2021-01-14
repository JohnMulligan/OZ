import json
import requests
import urllib
import re
from bs4 import BeautifulSoup

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

def build_url(this_base_url, path='',args_dict={}):
	url_parts = list(urllib.parse.urlparse(this_base_url))
	url_parts[2] = path
	url_parts[4] = urllib.parse.urlencode(args_dict)
	return urllib.parse.urlunparse(url_parts)

#path is like '/groups/12345/items'
#start parameter allows for pagination
def zotero_get_group_items(get_all=False):
	print('collecting zotero items')
	params=zotero_credentials
	args_dict={}
	start=0
	all_results=[]
	while True:
		args_dict['start']=start
		this_url=build_url(base_url,'/groups/'+str(group_id)+'/items/',args_dict)
		#print(this_url)
		response=requests.get(this_url,params=params)
		headers=response.headers
		j=json.loads(response.text)
		'''for i in j:
			print(i['key'])'''
		if len(j)>0:
			all_results += j
			start+=len(j)
		else:
			break
		
		if get_all==False:
			break
		print('collected ',len(all_results))
	
	return all_results
	
#not necessary if we're scraping all the items -- parent id's are baked into child items in ['data']['parentitem']
def zotero_get_children(item_ids):
	children=[]
	params=zotero_credentials
	args_dict={'include':'data,citation'}
	for id in item_ids:
		#"start" is the zotero api's offset parameter
		start=0
		while True:
			args_dict['start']=start
			this_url=build_url(base_url,'/groups/'+str(group_id)+'/items/'+str(id)+'/children',args_dict)
			#print(this_url)
			response=requests.get(this_url,params=params)
			headers=response.headers
			try:
				j=json.loads(response.text)
			
				'''for i in j:
					print(i['key'])'''
				if len(j)>0:
					children.append(j)
					start+=len(j)
				else:
					break
			except:
				print("error with: ",this_url,response)
				break
	return children


def zotero_download_attachment(item):
	downloadlink=item['downloadlink']
	params=zotero_credentials
	print("downloading %s" %this_url)
	response=requests.get(this_url,allow_redirects=True)
	if response.code!=200:
		return None
	else:
		try:
			fname=item['title']
		except:
			fname="tmp_download"
		open(fname,'wb').write(response.content)
		return fname


#this is hard-coded but the data is rather uneven and i'm finding understanding its structure logically to be difficult
def zotero_format_items(items):
	formatted_items=[]
	#hard-coded zotero item reader
	for item in items:
		i={}
		i['zotero_id']=item['key']
		i['url']=re.sub('//api.zotero.org','//www.zotero.org',item['links']['self']['href'])
		item_type=item['data']['itemType']
		i['item_type']=item_type
		i['modified']=item['data']['dateModified']
		try:
			i['parentItem']=item['data']['parentItem']
		except:
			pass
		if item_type=='note':
			#print(item['key'])
			note_html=item['data']['note']
			try:
				soup=BeautifulSoup(note_html,features="html.parser")
				#print(soup.text,item['links']['self']['href'])
				ptags=soup.find_all('p')
				paragraphs=[i.text for i in ptags]
				title=paragraphs[0]
				#handle short titles of lack of linebreaking
				#which is rather common in zotero notes
				if len(title)<=20:
					i['title']=title
					note='\n'.join(paragraphs[1:])
				else:
					i['title']=title[0:20]
					note='\n'.join(paragraphs)

				if note!='':
					i['note']=note
			except:
				i['note']=note_html
		elif item_type=='attachment':
			try:
				i['title']=item['data']['title']
			except:
				pass
			try:
				i['downloadlink']=item['links']['enclosure']['href']
			except:
				pass
		else:
			abstractNote=item['data']['abstractNote']
			if abstractNote!='':
				i['abstract']=abstractNote
			title=item['data']['title']
			if title!='':
				i['title']=title
			
			try:
				i['date']=int(re.search('[0-9]{4}',item['data']['date']).group(0))
			except:
				pass
			try:
				authors=[]
				for creator in item['data']['creators']:
					nameparts=[]
					for a in ['firstName','lastName']:
						nameparts.append(creator[a])
					authors.append(' '.join(nameparts))
				if authors!=[]:
					i['authors']=authors
			except:
				pass
			try:
				i['citation']=item['citation']
			except:
				pass
		formatted_items.append(i)
	return(formatted_items)