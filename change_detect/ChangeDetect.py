import hashlib
import os
import requests
import json
from bs4 import BeautifulSoup
from urllib.request import urlopen

def check_html(url, check_line, original_element):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    current_line = str(soup.find(original_element))

    if current_line == check_line:
        print("No changes detected")
        print(f"Current website says: {current_line}")
        return False
    else:
        print("Website changed. Notifying user")
        print(f"Current website says: {current_line}")
        return True


# Only use if the site has no constantly changing elements such as time
def hash_site(url, unchanged_hash):
    hashable_response = urlopen(url).read()
    currentHash = hashlib.sha224(hashable_response).hexdigest()
    if currentHash == unchanged_hash:
        print("No changes detected")
        print(f"Current hash {currentHash}")
        return False
    else:
        print("Website changed. Notifying user")
        print(f"Current hash {currentHash} \n original hash: {unchanged_hash}")
        return True


def find_on_site(url, sentence):
    req = requests.Request(url, headers={'User-Agent': 'AWS Lambda'})
    site = str(urlopen(req).read())
    if sentence in site:
        print(f"Expected '{sentence}' found at {str(datetime.now())} on {url}.")
        return False
    else:
        print("changes detected")
        print(f"{sentence} not found at {str(datetime.now())} on {url}.")
        return True


def post_message_to_slack(text, SLACK_WEBHOOK):
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
        return "Slack message send"


def lambda_handler(event, context):
    url = event['url']
    SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
    phone_nr = os.environ.get('phone_nr')

    # Check types: html/hash/search
    if event['check_type'] == "html":
        if check_html(url, event['check_line'], event['original_element']):
            post_message_to_slack(f"{url} html change detected", SLACK_WEBHOOK)
            return 'html change found!'
        else:
            return f'No html changes detected for {url}'

    if event['check_type'] == "hash":
        if hash_site(url, event['unchanged_hash']):
            post_message_to_slack(f"{url} hash change detected", SLACK_WEBHOOK)
            # boto3.client('sns').publish(PhoneNumber=phone_nr, Message=event['message'])
            return 'Hash change found!'
        else:
            return f'No hash changes detected for {url}'

    if event['check_type'] == "search":
        if find_on_site(url, event['sentence']):
            post_message_to_slack(f"{url} hash change detected", SLACK_WEBHOOK)
            return 'Hash change found!'
        else:
            return f'No hash changes detected for {url}'

    else:
        return "No checktype provided: html or hash"


tuinwijck_event = {
    "check_type": "hash",
    "url": "https://www.tuinwijck.nl/huisjes-te-koop",
    "unchanged_hash": "845124c335ba7e9091b3b739dae67ec6055de3d027b0093e5f2a7859"
}

# lambda_handler(tuinwijck_event, "context")
