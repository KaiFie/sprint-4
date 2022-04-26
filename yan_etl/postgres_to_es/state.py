import datetime
import json
import logging
from typing import Any, Optional


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            encoded_object = obj.isoformat()
        else:
            encoded_object = json.JSONEncoder.default(self, obj)
        return encoded_object


class DateTimeDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):

        for key, value in obj.items():
            try:
                obj[key] = datetime.datetime.fromisoformat(value)
            except Exception as e:
                logging.exception(e, exc_info=True)

        return obj


class JsonFileStorage:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def save_state(self, state: dict) -> None:
        with open(self.file_path, 'w') as f:
            json.dump(state, f, cls=DateTimeEncoder)

    def retrieve_state(self) -> dict:
        try:
            with open(self.file_path) as json_file:
                return json.load(json_file, cls=DateTimeDecoder)
        except FileNotFoundError:
            return {}


class State:

    def __init__(self, path: Optional[str]):
        if path is None:
            path = 'state.json'
        self.storage = JsonFileStorage(path)

    def set_state(self, key: str, value: Any) -> None:
        state = self.storage.retrieve_state()
        state[key] = value
        self.storage.save_state(state)

    def get_state(self, key: str, default: Any) -> Any:
        state = self.storage.retrieve_state()
        return state.get(key, default)
