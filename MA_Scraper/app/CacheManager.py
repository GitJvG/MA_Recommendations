from datetime import datetime
from flask import request

class CacheManager:
    def __init__(self):
        self.caches = {}

    def reset_cache(self, route=None):
        route_name = route if route else request.path
        if route_name in self.caches:
            self.caches[route_name] = {"date": None, "data": None}

    def get_cache(self):
        route_name = request.path
        cache = self.caches.get(route_name)

        if cache and cache["date"] == datetime.today().date() and cache["data"] is not None:
            return cache["data"]
        else:
            return None

    def set_cache(self, data):
        route_name = request.path
        self.caches[route_name] = {
            "date": datetime.today().date(),
            "data": data
        }