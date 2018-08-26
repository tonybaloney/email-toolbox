import yaml
from pprint import pprint
import json
import pandas as pd

with open(".config.yml", "r") as config_f:
    config = yaml.load(config_f)

items = []
for target in config["folders"]:
    with open("inbox.{0}.cache".format(target), "r") as cache:
        folder = json.load(cache)
        for item in folder:
            item["folder"] = target
            if target == "Trash":
                item['outcome'] = "delete"
            del item['text_body']
    items.extend(folder)

df = pd.DataFrame(items)
writer = pd.ExcelWriter("output.xlsx")
df.to_excel(writer, "Sheet1")
writer.save()
