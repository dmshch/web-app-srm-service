# Copyright © 2020 Dmitrii Shcherbakov. All rights reserved. 

import json
import pathlib

def load_settings():
    path = str(pathlib.Path().absolute()) + "/web/settings.json"
    data = dict()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Failed to load settings. Check the correctness of the settings file 'web/settings.json'.")
    except:
        print("Check the syntax of the file 'web/settings.json'")
    return data
