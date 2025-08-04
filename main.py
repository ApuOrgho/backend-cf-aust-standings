from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import List, Optional
from pydantic import BaseModel


app = FastAPI()

# Allow frontend requests (localhost dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Example AUST handles (can be replaced by reading CSV later)
aust_handles = [
    "mursalin", "sami_01", "rifat_69", "tanvir.cse", "hello_world_aust"
]
aust_set = set(handle.lower() for handle in aust_handles)


class Participant(BaseModel):
    handle: str
    rank: int
    points: float
    penalty: Optional[int] = None


class StandingsResponse(BaseModel):
    contest_name: str
    global_standings: List[Participant]
    aust_standings: List[Participant]
    aust_avg: Optional[float] = None


@app.get("/standings/{contest_id}", response_model=StandingsResponse)
async def get_standings(contest_id: int):
    url = (
        f"https://codeforces.com/api/contest.standings?"
        f"contestId={contest_id}&from=1&count=30000&showUnofficial=false"
    )
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            data = r.json()  # <--- no await here
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch standings: {str(e)}")

    if data.get('status') != 'OK':
        raise HTTPException(status_code=404, detail="Contest not found or failed to fetch standings.")

    rows = data['result']['rows']
    contest_name = data['result']['contest']['name']
    global_standings = []
    aust_standings = []
    aust_points_sum = 0
    aust_count = 0

    is_penalty_based = any(k in contest_name.lower() for k in ["edu", "div.3", "div.4"])

    for row in rows:
        handle = row["party"]["members"][0]["handle"]
        rank = row["rank"]
        points = row.get("points", 0)

        penalty = None
        if is_penalty_based:
            penalty = 0
            for result in row.get("problemResults", []):
                if result.get("points", 0) > 0:
                    time_sec = result.get("bestSubmissionTimeSeconds", 0)
                    wrong_attempts = result.get("rejectedAttemptCount", 0)
                    penalty += time_sec + (wrong_attempts * 20 * 60)

        participant = Participant(
            handle=handle,
            rank=rank,
            points=points,
            penalty=penalty
        )

        global_standings.append(participant)

        if handle.lower() in aust_set:
            aust_standings.append(participant)
            aust_points_sum += points
            aust_count += 1

    aust_avg = round(aust_points_sum / aust_count, 2) if aust_count else None

    return StandingsResponse(
        contest_name=contest_name,
        global_standings=global_standings,
        aust_standings=aust_standings,
        aust_avg=aust_avg
    )
