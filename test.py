from exchangelib import Account, ServiceAccount, Configuration, DELEGATE, EWSTimeZone
from exchangelib.items import Message
import exchangelib.queryset
import yaml
from pprint import pprint
import json
import requests

with open(".config.yml", "r") as config_f:
    config = yaml.load(config_f)

apim_key = config["apim_key"]

# fields of an email to serialise
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

account = connect(config)


def related(folder, item):
    try:
        item = folder.get(in_reply_to=item.message_id)
        return item.datetime_sent
    except exchangelib.queryset.DoesNotExist:
        return None


for target in config["folders"][:1]:
    folder = account.root.get_folder_by_name(target)
    outbox = account.sent
    # .inbox.all().order_by('-datetime_received')[:100]
    item = folder.get(subject="IMPORTANT SUMMARY of GDC business Challenges and Learning Intervention Development") # .only(*fields)
    reply = related(outbox, item)
    if reply:
        print(item.datetime_sent - item.datetime_received)