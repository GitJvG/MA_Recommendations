from datetime import datetime

class CacheManager:
    def __init__(self):
        self.caches = {}

    def reset_cache(self, route_name):
        """Reset the cache for a specific route."""
        if route_name in self.caches:
            self.caches[route_name] = {"date": None, "data": None}

    def get_cache(self, route_name):
        """Return the cache for a specific route."""
        return self.caches.get(route_name, {"date": None, "data": None})

    def set_cache(self, route_name, data):
        """Set the cache with new data for a specific route."""
        self.caches[route_name] = {
            "date": datetime.today().date(),
            "data": data
        }

    def is_cache_valid(self, route_name):
        """Check if the cache for a specific route is valid for today."""
        cache = self.caches.get(route_name)
        if cache:
            return cache["date"] == datetime.today().date() and cache["data"] is not None
        return False

cache_manager = CacheManager()
