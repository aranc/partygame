import inspect

# Custom decorator to decorate the methods and track them
def expose_to_agent(func):
    func._is_tracked = True  # Mark the function as tracked
    return func

# Base class to store and retrieve the source of decorated methods
class SourceTracker:
    @classmethod
    def get_tracked_methods_source(cls):
        """
        Get the source code of all tracked (decorated) methods in the class
        and its subclasses.
        """
        tracked_methods = {}
        # Loop through all attributes of the class
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if getattr(method, '_is_tracked', False):
                # Get the source code of the tracked method
                source_code = inspect.getsource(method)
                tracked_methods[name] = source_code

        return tracked_methods

# Example subclass using the custom decorator
class MyClass(SourceTracker):
    @expose_to_agent
    def method_one(self):
        # Method 1 code
        print("This is method one")
    
    def method_two(self):
        # Not tracked
        print("This is method two")
    
    @expose_to_agent
    def method_three(self):
        # Method 3 code
        print("This is method three")

# Example usage
if __name__ == "__main__":
    # Get the source code of all decorated methods
    tracked_methods_source = MyClass.get_tracked_methods_source()
    
    # Print the source code of all tracked methods
    for method_name, source in tracked_methods_source.items():
        print(f"Source code for method: {method_name}")
        print(source)
        print("-" * 40)

