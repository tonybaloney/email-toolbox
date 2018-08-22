from exchangelib import Account, ServiceAccount, Configuration, DELEGATE, EWSTimeZone
from exchangelib.items import Message
import yaml
from pprint import pprint
import json
import requests

with open(".config.yml", "r") as config_f:
    config = yaml.load(config_f)
apim_key = config["apim_key"]


def connect(config):
    _credentials = ServiceAccount(
        username=config["username"], password=config["password"]
    )
    timezone = EWSTimeZone.timezone(config["timezone"])
    try:
        server = config["server"]
        autodiscover = False if server is not None else True
    except KeyError:
        autodiscover = True

    if autodiscover:
        account = Account(
            primary_smtp_address=config["primary_smtp_address"],
            credentials=_credentials,
            autodiscover=autodiscover,
            access_type=DELEGATE,
        )
    else:
        ms_config = Configuration(server=server, credentials=_credentials)
        account = Account(
            primary_smtp_address=config["primary_smtp_address"],
            config=ms_config,
            autodiscover=False,
            access_type=DELEGATE,
        )
    return account


def simple(obj, fields):
    s = {}
    for field in fields:
        s[field] = getattr(obj, field)
        if field == "text_body":
            # strip conversations..
            if "\r\n\r\nFrom:" in s[field]:
                s[field] = s[field].split("\r\n\r\nFrom:")[0]
    return s


def get_entities(cache):
    # Extract key phrases
    documents = []
    id = 1
    for item in cache:
        documents.append({"language": "en", "id": id, "text": item["text_body"]})
        id += 1
    request = {"documents": documents}
    headers = {
        "content-type": "application/json",
        "ocp-apim-subscription-key": apim_key,
    }
    response = requests.post(
        "https://southeastasia.api.cognitive.microsoft.com/text/analytics/v2.0/keyPhrases",
        json=request,
        headers=headers,
    )
    result = response.json()
    id = 0
    for item in cache:
        item["keyPhrases"] = result["documents"][id]["keyPhrases"]
        id += 1
    return cache


def normalise(cache):
    # Remove common entities from key phrases
    size = len(cache)
    remove = []  # phrases to remove
    # Use first as the index
    for phrase in cache[0]["keyPhrases"]:
        if sum([1 for item in cache if phrase in item["keyPhrases"]]) >= size:
            remove.append(phrase)
    print(remove)
    for item in cache:
        item["keyPhrases"] = [
            phrase for phrase in item["keyPhrases"] if phrase not in remove
        ]
    return cache


account = connect(config)
fields = (
    "text_body",
    "subject",
    "size",
    "categories",
    "importance",
    "in_reply_to",
    "reminder_is_set",
    "has_attachments",
)

for target in config["folders"]:
    folder = account.root.get_folder_by_name(target)
    # .inbox.all().order_by('-datetime_received')[:100]
    items = folder.all().only(*fields)
    cache = [simple(item, fields) for item in items[:5] if isinstance(item, Message)]
    cache = get_entities(cache)
    cache = normalise(cache)

    with open("inbox.{0}.cache".format(target), "w") as out:
        json.dump(cache, out)
