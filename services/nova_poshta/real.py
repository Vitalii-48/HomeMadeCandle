import requests
from flask import current_app

API_URL = "https://api.novaposhta.ua/v2.0/json/"

def _post(model, method, props={}):
    payload = {
        "apiKey": current_app.config["NOVA_POSHTA_API_KEY"],
        "modelName": model,
        "calledMethod": method,
        "methodProperties": props
    }
    resp = requests.post(API_URL, json=payload)
    return resp.json().get("data", [])

def search_cities(query: str) -> list:
    raw = _post("Address", "searchSettlements", {
        "CityName": query,
        "Limit": 10
    })
    addresses = raw[0].get("Addresses", []) if raw else []
    return [{"ref": a["DeliveryCity"], "name": a["Present"]} for a in addresses]

def get_warehouses(city_ref: str) -> list:
    raw = _post("AddressGeneral", "getWarehouses", {
        "CityRef": city_ref,
        "Limit": 50
    })
    return [{"ref": w["Ref"], "name": w["Description"]} for w in raw]