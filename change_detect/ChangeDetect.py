import hashlib
import os
from pprint import pprint

import boto3
import requests
import json
from bs4 import BeautifulSoup
from urllib.request import urlopen

# Only use if the site has no constantly changing elements such as time
def hash_site(url, unchanged_hash):
    hashable_response = urlopen(url).read()
    currentHash = hashlib.sha224(hashable_response).hexdigest()
    if currentHash == unchanged_hash:
        print(f"No changes detected at {url}")
        print(f"Current hash {currentHash}")
        return False
    else:
        print(f"{url} changed. Notifying user")
        print(f"Current hash {currentHash} \n original hash: {unchanged_hash}")
        return currentHash


def check_html(url, check_line, html_element):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    current_line = str(soup.find(html_element))

    if current_line == check_line:
        print(f"No html changes detected at {url}")
        return False
    else:
        print(f"{url} changed. Notifying user")
        print(f"Currently {url} says: {current_line}")
        return current_line


def find_on_site(url, check_line):
    site = str(urlopen(url).read())
    print(site)
    if check_line in site:
        print(f"Expected '{check_line}' found at {url}.")
        return False
    else:
        print("changes detected")
        print(f"{check_line} not found at {url}.")
        return True


def post_message_to_slack(text, check_type):
    SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
    slack_data = {'text': text}
    response = requests.post(
               SLACK_WEBHOOK,
               data=json.dumps(slack_data),
               headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
    else:
        print("Slack message send", text)
        return f"{check_type} change found!"


def read_dynamodb(table_name, id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    item = table.get_item(Key={'id': id})["Item"]
    print(item)
    return item


def scan_dynamodb(table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    items = table.scan()["Items"]
    return items


def write_dynamodb(url, check_type, line, html_element=None):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("WebsiteChecktable")
    response = table.update_item(
        Key={'url': url},
        UpdateExpression="set check_type=:c, line=:l, html_element=:h",
        ExpressionAttributeValues={
            ':c': check_type,
            ':l': line,
            ':h': html_element
        }
    )
    print(f"Successful DynamoDB write to {url} with {line}")
    print(response)
# write_dynamodb('https://www.hvdveer.nl', 'hash', '015c0f79ba863036c0b08d60f56a5601f65d326961feffd110dce526')

def check_type(item):
    url = item["url"]
    check_type = item['check_type']
    # Differentiate check types: html/hash/search
    if item['check_type'] == "html":
        line = check_html(url, item['line'], item['html_element'])
        if line:
            post_message_to_slack(f"{url} {check_type} change detected", check_type)
            write_dynamodb(url, check_type, line, item['html_element'])
        else:
            return f'No html changes detected for {url}'

    if item['check_type'] == "hash":
        line = hash_site(url, item['line'])
        if line:
            # boto3.client('sns').publish(PhoneNumber=phone_nr, Message=item['message'])
            post_message_to_slack(f"{url} {check_type} change detected", check_type)
            write_dynamodb(url, check_type, line)
        else:
            return f'No hash changes detected for {url}'

    if item['check_type'] == "search":
        if find_on_site(url, item['line']):
            return post_message_to_slack(f"{url} {check_type} change detected. Didn't find {item['line']} at {url}.", check_type)
        else:
            return f"Found expected sentence at {url}: {item['line']}"

    else:
        return "No checktype provided, should be: html/hash/search"


def lambda_handler():
    phone_nr = os.environ.get('phone_nr')
    items = scan_dynamodb("WebsiteChecktable")
    for item in items:
        check_type(item)



tuinwijck_event = {
    "check_type": "hash",
    "url": "https://www.tuinwijck.nl/huisjes-te-koop",
    "unchanged_hash": "78191fc6598b36b1dc6a825f09220be62d650a910a06eca75f14338b"
}

piccardhof = {
    "check_type": "search",
    "url": "https://www.piccardthof.nl/huisjes-te-koop/",
    "line": "ER ZIJN OP DIT MOMENT GEEN HUISJES TE KOOP"
}

if __name__ == '__main__':
    lambda_handler()
    # read_dynamodb("WebsiteChecklines", "tuinwijck")
