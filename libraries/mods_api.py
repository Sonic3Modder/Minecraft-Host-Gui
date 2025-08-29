import json
import os
import urllib.parse
import urllib.request


MODRINTH_API = "https://api.modrinth.com/v2"
CURSEFORGE_API = "https://api.curseforge.com/v1"


class HttpError(Exception):
    pass


def _http_get(url: str, headers: dict | None = None) -> dict:
    request = urllib.request.Request(url)
    if headers:
        for k, v in headers.items():
            request.add_header(k, v)
    try:
        with urllib.request.urlopen(request) as response:
            data = response.read().decode("utf-8")
            return json.loads(data)
    except Exception as exc:
        raise HttpError(str(exc))


def _http_get_bytes(url: str, headers: dict | None = None) -> bytes:
    request = urllib.request.Request(url)
    if headers:
        for k, v in headers.items():
            request.add_header(k, v)
    with urllib.request.urlopen(request) as response:
        return response.read()


# Modrinth
def modrinth_search_projects(query: str, project_type: str, index: str = "relevance", limit: int = 50) -> list[dict]:
    params = {
        "query": query or "",
        "facets": json.dumps([[f"project_type:{project_type}"]]),
        "index": index,
        "limit": str(limit)
    }
    url = f"{MODRINTH_API}/search?{urllib.parse.urlencode(params)}"
    payload = _http_get(url)
    return payload.get("hits", [])


def modrinth_get_project(project_id: str) -> dict:
    url = f"{MODRINTH_API}/project/{project_id}"
    return _http_get(url)


def modrinth_get_versions(project_id: str, loaders: list[str] | None = None, game_versions: list[str] | None = None) -> list[dict]:
    params = {}
    if loaders:
        params["loaders"] = json.dumps(loaders)
    if game_versions:
        params["game_versions"] = json.dumps(game_versions)
    qs = urllib.parse.urlencode(params)
    url = f"{MODRINTH_API}/project/{project_id}/version" + (f"?{qs}" if qs else "")
    return _http_get(url)


# CurseForge
def curseforge_search_projects(query: str, section: str, api_key: str, sort_field: int | None = None, page_size: int = 50) -> list[dict]:
    # section: mods=6, plugins(bukkit)=5
    section_id = 6 if section == "mods" else 5
    params_dict = {"gameId": 432, "searchFilter": query or "", "classId": section_id, "pageSize": page_size}
    if sort_field is not None:
        params_dict["sortField"] = sort_field
    params = urllib.parse.urlencode(params_dict)
    url = f"{CURSEFORGE_API}/mods/search?{params}"
    payload = _http_get(url, headers={"x-api-key": api_key})
    return payload.get("data", [])


def curseforge_get_project(mod_id: int, api_key: str) -> dict:
    url = f"{CURSEFORGE_API}/mods/{mod_id}"
    payload = _http_get(url, headers={"x-api-key": api_key})
    return payload.get("data", {})


def curseforge_get_files(mod_id: int, api_key: str) -> list[dict]:
    url = f"{CURSEFORGE_API}/mods/{mod_id}/files"
    payload = _http_get(url, headers={"x-api-key": api_key})
    return payload.get("data", [])


def download_file(url: str, destination_path: str) -> None:
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    with urllib.request.urlopen(url) as response, open(destination_path, "wb") as out_file:
        out_file.write(response.read())


def fetch_bytes(url: str, headers: dict | None = None) -> bytes:
    return _http_get_bytes(url, headers=headers)


