import json


def write_json(data, path):
    with path.open('w') as f:
        json.dump(data, f, indent='    ', sort_keys=True)
