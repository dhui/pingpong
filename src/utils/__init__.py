import simplejson as json

from django.http import HttpResponse

def render_to_json(data):
    return HttpResponse(json.dumps(data), mimetype="application/json")
