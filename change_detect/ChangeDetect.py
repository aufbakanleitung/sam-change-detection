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


def post_message_to_slack(text, SLACK_WEBHOOK, check_type):
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


def lambda_handler(event, context):
    url = event['url']
    SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
    phone_nr = os.environ.get('phone_nr')

    # Differentiate check types: html/hash/search
    if event['check_type'] == "html":
        if check_html(url, event['check_line'], event['original_element']):
            return post_message_to_slack(f"{url} html change detected", SLACK_WEBHOOK, event['check_type'])
        else:
            return f'No html changes detected for {url}'

    if event['check_type'] == "hash":
        if hash_site(url, event['unchanged_hash']):
            # boto3.client('sns').publish(PhoneNumber=phone_nr, Message=event['message'])
            return post_message_to_slack(f"{url} hash change detected", SLACK_WEBHOOK, event['check_type'])
        else:
            return f'No hash changes detected for {url}'

    if event['check_type'] == "search":
        if find_on_site(url, event['check_line']):
            return f"Found expected sentence at {url}: {event['check_line']}"
        else:
            return post_message_to_slack(f"Search change detected. Didn't find {event['check_line']} at {url}.", SLACK_WEBHOOK, event['check_type'])

    else:
        return "No checktype provided, should be: html/hash/search"


tuinwijck_event = {
    "check_type": "hash",
    "url": "https://www.tuinwijck.nl/huisjes-te-koop",
    "unchanged_hash": "78191fc6598b36b1dc6a825f09220be62d650a910a06eca75f14338b"
}

piccardhof = {
    "check_type": "search",
    "url": "https://www.piccardthof.nl/huisjes-te-koop/",
    "check_line": "ER ZIJN OP DIT MOMENT GEEN HUISJES TE KOOP"
}

# lambda_handler(tuinwijck_event, "context")
