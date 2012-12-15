import simplejson as json

from django.http import HttpResponse

def render_to_json(data):
    return HttpResponse(json.dumps(data), mimetype="application/json")

def cached_property(f):
    def get(self):
        try:
            return self._property_cache[f]
        except AttributeError:
            self._property_cache = {}
            x = self._property_cache[f] = f(self)
            return x
        except KeyError:
            x = self._property_cache[f] = f(self)
            return x

    return property(get)
