import requests


def format_dt(value):
    return f"0{value}" if 10 > value >= 0 else value


def api_request(method, path, json=None, params=None):
    api_endpoint = "https://ki2-api.deta.dev"
    response = requests.request(
        method=method,
        url=f'{api_endpoint}/{path}/',
        params=params,
        json=json
    )
    return response.json()
