from SourceTracker import expose_to_agent
from CachedAnnotations import CachedAnnotations

class SubClass(CachedAnnotations):
    def __init__(self):
        super().__init__()

    @expose_to_agent
    def add(self, a: int, b: int) -> int:
        return a + b

    @expose_to_agent
    def get_weather(self, city: str) -> str:
        if city == "London":
            return "Rainy"
        return "Sunny"

subClass = SubClass()

res = subClass.get_tracked_methods_source_and_json_annotation()
print(f"Length of Tracked Methods: {len(res)}")

for method_name, method_data in res.items():
    print(f"Method: {method_name}")
    print(f"Source Code:\n{method_data['source']}")
    print(f"JSON Annotation:\n{method_data['json_annotation']}")
    print("-" * 40)
