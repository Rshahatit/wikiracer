from django.http import JsonResponse
from find_path.scripts.async_sol.main import start
from find_path.scripts.parse_input import parse_input
import json
import asyncio

def index(request):
    body = json.loads(request.body)
    source = parse_input(body["source"])
    destination = parse_input(body["destination"])
    print(f'starting search from {source} to {destination}')
    # I was going to put this as a requirement but changed my mind
    # maybe someone wants to see what the path is from a page to itself.
    # if source == destination: 
    #     payload = {"error":True, "message" : "Source and destination should not be the same"}
    #     return JsonResponse(payload, status=400) 
    if source == 0 or destination == 0:
        payload = {"error": True, "message" : "You must enter a valid wikipedia link"}
        return JsonResponse(payload, status=400)
    else:
        return JsonResponse(start(source, destination))
