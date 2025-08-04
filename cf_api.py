import httpx
from typing import List

BASE_URL = "https://codeforces.com/api"

async def get_contest_list():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/contest.list")
        r.raise_for_status()
        data = await r.json()
        if data["status"] != "OK":
            raise Exception("Failed to fetch contest list")
        return data["result"]

async def get_contest_standings(contest_id: int, handles: List[str]):
    handle_str = ";".join(handles)
    params = {
        "contestId": contest_id,
        "handles": handle_str,
        "showUnofficial": "true"
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/contest.standings", params=params)
        r.raise_for_status()
        data = await r.json()
        if data["status"] != "OK":
            raise Exception(f"Failed to fetch standings for contest {contest_id}")
        return data["result"]
