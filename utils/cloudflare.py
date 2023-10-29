import os
import requests
from pymongo.mongo_client import MongoClient

CLOUDFLARE_EMAIL = os.getenv('CLOUDFLARE_EMAIL')
CLOUDFLARE_TOKEN = os.getenv('CLOUDFLARE_TOKEN')
CLOUDFLARE_ZONE_ID = os.getenv('CLOUDFLARE_ZONE_ID')
DB_URL = os.getenv('MONGODB_URL')
HOST_IP = os.getenv('HOST_IP')
client = MongoClient(DB_URL)
database = client['dns_record']

assert client is not None, 'DB connect fail'


def modify_domain_on_cloudflare(domain: str, method: str = 'POST' or 'DELETE'):
    url = f'https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records'
    
    if method == 'DELETE':
        zone_id = database['domain'].find_one({'domain': domain})['zone_id']
        url += f'/{zone_id}'

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Key": CLOUDFLARE_TOKEN,
        "X-Auth-Email": CLOUDFLARE_EMAIL,
    }


    post_body = {
        'content': HOST_IP,
        'name': domain.split('.')[0],
        'type': 'A',
        'proxied': True,
    }

    if method == 'POST':
        return requests.post(url, headers=headers, json=post_body)
    if method == 'DELETE':
        return requests.delete(url, headers=headers)
    raise Exception('method not found')

def modify_domain_on_database(domain: str, zone_id: str, user_email: str, method: str):
    html_template = '<!DOCTYPE html><html><body><h1>My First Web!</h1></body></html>'
    collection = database['domain']
    if method == 'POST':
        if collection.find_one({'domain': domain}) == None:
            collection.insert_one({'email': user_email, 'domain': domain, 'zone_id': zone_id, 'html': html_template})
        else:
            raise Exception('domain already exist')
    if method == 'DELETE':
        if collection.find_one({'domain': domain}) != None:
            collection.delete_one({'domain': domain})
        else:
            raise Exception('domain not exist')
        
def modify_user_domain_on_database(domain: str, user_email: str, method: str):
    collection = database['user']
    
    if method == 'POST':
        data = collection.find_one({'email': user_email})
        if data == None:
            collection.insert_one({'email': user_email, 'domain_list': [domain]})
        elif domain not in data['domain_list']:
            collection.update_one({'email': user_email}, {'$addToSet': {'domain_list': domain}})
    if method == 'DELETE':
        collection.update_one({'email': user_email}, {'$pull': {'domain_list': domain}})

def modify_domain_data(domain: str, user_email: str, method: str):
    response = modify_domain_on_cloudflare(domain, method)
    print('rsp af')
    print(response.json())
    if not response.ok:
        raise Exception(response.json()['errors'][0]['message'])

    zone_id = response.json()['result']['id']
    modify_domain_on_database(domain, zone_id, user_email, method)
    modify_user_domain_on_database(domain, user_email, method)

def get_domain(user_email: str):
    collection = database['user']
    if collection.find_one({'email': user_email}) == None:
        return []
    return collection.find_one({'email': user_email})['domain_list']

def get_html(domain: str):
    collection = database['domain']
    document = collection.find_one({'domain': domain})

    if document == None:
        return '<!DOCTYPE html><html><body><h1>Domain Not Found!</h1></body></html>'
    return document['html']

def update_html(domain: str, html: str):
    collection = database['domain']
    if collection.find_one({'domain': domain}) == None:
        raise Exception('domain not found')
    collection.update_one({'domain': domain}, {'$set': {'html': html}})