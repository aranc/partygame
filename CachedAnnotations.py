import os
import json
import inspect
import importlib
import pickle
import fcntl
from collections import OrderedDict
from SourceTracker import SourceTracker
from SchemaGenerator import generate_schema

# Default connector and model for generating JSON annotations
DEFAULT_ANNOTATION_CONNECTOR = 'openai'
DEFAULT_ANNOTATION_MODEL = 'gpt-4o'

# Path to the cache file
CACHE_FILEPATH = os.path.expanduser('~/.cached_annotations.pkl')

class LRUCache:
    """ Simple LRU cache to store function annotations """
    def __init__(self, capacity: int = 1024, cache_filepath: str = CACHE_FILEPATH):
        self.cache_filepath = cache_filepath
        self.cache = OrderedDict()
        self.capacity = capacity

        # if CACHE_FILEPATH does not exist, create it
        if not os.path.exists(self.cache_filepath):
            with open(self.cache_filepath, 'wb'):
                pass

    def get(self, key):
        # Open the file and lock it exclusively for reading and writing
        with open(self.cache_filepath, 'rb+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)  # Exclusive lock for both reading and writing
            try:
                self.cache = pickle.load(f)
            except EOFError:
                # Handle case where file is empty
                self.cache = OrderedDict()

            if key not in self.cache:
                fcntl.flock(f, fcntl.LOCK_UN)  # Unlock before returning
                return None

            # Move the key to the end to maintain LRU order
            self.cache.move_to_end(key)

            # Go back to the beginning of the file and overwrite the cache
            f.seek(0)
            pickle.dump(self.cache, f)
            f.truncate()  # Truncate the file in case the new cache is smaller

            fcntl.flock(f, fcntl.LOCK_UN)  # Release the lock

        return self.cache[key]

    def put(self, key, value):
        # Open the file and lock it exclusively for reading and writing
        with open(self.cache_filepath, 'rb+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)  # Exclusive lock for both reading and writing
            try:
                self.cache = pickle.load(f)
            except EOFError:
                # Handle case where file is empty
                self.cache = OrderedDict()

            # Add or update the value in the cache
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                # Remove the least recently used (LRU) item
                self.cache.popitem(last=False)

            # Go back to the beginning of the file and overwrite the cache
            f.seek(0)
            pickle.dump(self.cache, f)
            f.truncate()  # Truncate the file in case the new cache is smaller

            fcntl.flock(f, fcntl.LOCK_UN)  # Release the lock


class CachedAnnotations(SourceTracker):
    def __init__(self, annotation_connector: str = DEFAULT_ANNOTATION_CONNECTOR, annotation_model: str = DEFAULT_ANNOTATION_MODEL, cache_filepath: str = CACHE_FILEPATH):
        super().__init__()
        self.annotation_model = annotation_model
        self.annotation_connector = annotation_connector
        self.json_cache = LRUCache(cache_filepath=cache_filepath)

        # Dynamically load the annotation connector (e.g., openai.py)
        connector_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'connectors', f'{annotation_connector}.py'))
        spec = importlib.util.spec_from_file_location('annotation_connector', connector_path)
        self.annotation_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.annotation_module)

    def _generate_json_schema(self, func):
        """ Generates JSON schema for a function using OpenAI or a default connector """
        source_code = inspect.getsource(func)
        key = "\n".join([line for line in source_code.split("\n") if not line.strip() == "@expose_to_agent"])
        return generate_schema(source_code, connector=self.annotation_module, model=self.annotation_model)

    def annotate_function(self, func):
        """ Caches the JSON schema for a function, using the LRU cache """
        func_name = func.__name__
        key = inspect.getsource(func)
        cached_schema = self.json_cache.get(key)
        if not cached_schema:
            # Generate and cache the schema
            print("Generating JSON schema for function:", func_name)
            json_schema = self._generate_json_schema(func)
            self.json_cache.put(key, json_schema)
            return json_schema
        return cached_schema

    def get_tracked_methods_source_and_json_annotation(self):
        """
        Get the source code and json annotations of all tracked
        (decorated) methods in the class and its subclasses.
        """
        tracked_methods = self.get_tracked_methods_source()
        for method_name, method_source in tracked_methods.items():
            tracked_methods[method_name] = {
                'source': method_source,
                'json_annotation': self.annotate_function(getattr(self, method_name))
            }

        return tracked_methods

if __name__ == "__main__":
    print("Test chat connection with the connector:")
    ca = CachedAnnotations()
    print(ca.annotation_module.chat(model=ca.annotation_model, messages=[{"role": "system", "content": "Hello"}]))
    print()

    print("Test JSON annotation generation for a function:")
    def test_function(a: int, b: int) -> int:
        return a + b
    print(ca.annotate_function(test_function))
