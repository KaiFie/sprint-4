import abc
import json
from json import JSONDecodeError
from typing import Any


class BaseStorage:
    """Abstract class for persistent Storage."""

    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Store state to persistent storage."""
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Load state from persistent storage."""
        pass


class JsonFileStorage(BaseStorage):
    """Storage to keep serialized json on disk."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def retrieve_state(self) -> dict:
        try:
            with open(self.file_path, 'rb') as fs:
                text = fs.readline()
                return json.loads(text)
        except (FileNotFoundError, JSONDecodeError):
            return {}

    def save_state(self, state: dict) -> None:
        with open(self.file_path, 'w') as fs:
            fs.write(json.dumps(state))


class State:
    """
    Class to interact with persistent storage to keep state.
    """

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    def set_state(self, key: str, value: dict[str, Any] | list | Any) -> None:
        """
        Set state for key
        Args:
            key: any dict() supported key.
            value: any JSON serializable value.

        Returns:
            None
        """
        current_state = self.storage.retrieve_state()
        current_state[key] = value
        self.storage.save_state(current_state)

    def get_state(self, key: str) -> Any | None:
        """
        Get value by key from storage.
        Args:
            key: str

        Returns:
            value
        """
        current_state = self.storage.retrieve_state()
        return current_state.get(key, None)
