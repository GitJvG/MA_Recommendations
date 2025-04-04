from datetime import datetime
from flask import g, request

class CacheManager:
    def __init__(self):
        self.caches = {}

    def reset_cache(self, route=None):
        """Reset the cache for the current route and device."""
        route_name = route if route else request.path
        device = g.device
        if (route_name, device) in self.caches:
            self.caches[(route_name, device)] = {"date": None, "data": None}

    def get_cache(self):
        """Return the cache for the current route and device, if valid."""
        route_name = request.path
        device = g.device
        cache = self.caches.get((route_name, device))

        if cache and cache["date"] == datetime.today().date() and cache["data"] is not None:
            return cache["data"]
        else:
            return None

    def set_cache(self, data):
        """Set the cache with new data for the current route and device."""
        route_name = request.path
        device = g.device
        self.caches[(route_name, device)] = {
            "date": datetime.today().date(),
            "data": data
        }