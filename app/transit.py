"""Transit domain logic: static network data plus a deterministic live-data simulation.

The simulated timetable is derived only from the clock, so every instance of the
app (and every unit test that passes a fixed ``now_s``) sees the same service.
Services run all day on a fixed headway; this keeps demos and recordings from
showing an empty board at night.
"""
from __future__ import annotations

import math
import time

STOPS: dict[str, str] = {
    "S1": "Central Station",
    "S2": "Market Square",
    "S3": "City Hospital",
    "S4": "Tech Park",
    "S5": "University Campus",
    "S6": "Riverside Mall",
    "S7": "Stadium",
    "S8": "Airport Terminal",
}

ROUTES: dict[str, dict] = {
    "R1": {
        "name": "Blue Line Express",
        "colour": "blue",
        "stops": ["S1", "S2", "S4", "S6"],
        "headway_min": 10,
        "trip_min": 30,
    },
    "R2": {
        "name": "Green Loop",
        "colour": "green",
        "stops": ["S1", "S3", "S5", "S7"],
        "headway_min": 15,
        "trip_min": 40,
    },
    "R3": {
        "name": "Campus Shuttle",
        "colour": "amber",
        "stops": ["S4", "S5", "S6", "S8"],
        "headway_min": 20,
        "trip_min": 24,
    },
    "R4": {
        "name": "Airport Link",
        "colour": "red",
        "stops": ["S1", "S2", "S7", "S8"],
        "headway_min": 30,
        "trip_min": 36,
    },
}

OCCUPANCY = ("Low", "Medium", "High")


def _now(now_s: int | float | None) -> int:
    return int(time.time()) if now_s is None else int(now_s)


def stop_offset_s(route_id: str, stop_id: str) -> int:
    """Seconds after departure from the first stop at which a vehicle reaches ``stop_id``."""
    route = ROUTES[route_id]
    stops = route["stops"]
    index = stops.index(stop_id)
    return round(route["trip_min"] * 60 * index / (len(stops) - 1))


def list_routes() -> list[dict]:
    """Return every route with its ordered stops (used by the page and the API)."""
    return [
        {
            "id": route_id,
            "name": route["name"],
            "colour": route["colour"],
            "headway_min": route["headway_min"],
            "trip_min": route["trip_min"],
            "stops": [{"id": s, "name": STOPS[s]} for s in route["stops"]],
        }
        for route_id, route in ROUTES.items()
    ]


def validate_search(origin: str, destination: str) -> str | None:
    """Return an error message for an invalid journey search, or ``None`` if it is valid."""
    if origin not in STOPS or destination not in STOPS:
        return "Please choose a valid origin and destination stop."
    if origin == destination:
        return "Origin and destination must be different stops."
    return None


def next_arrivals(route_id: str, stop_id: str, now_s: int | float | None = None, count: int = 3) -> list[dict]:
    """Next ``count`` vehicles of a route reaching a stop, soonest first."""
    now = _now(now_s)
    route = ROUTES[route_id]
    headway = route["headway_min"] * 60
    offset = stop_offset_s(route_id, stop_id)
    first_k = math.ceil((now - offset) / headway)
    arrivals = []
    for i in range(count):
        eta_s = (first_k + i) * headway + offset - now
        arrivals.append(
            {
                "route_id": route_id,
                "route_name": route["name"],
                "colour": route["colour"],
                "eta_seconds": eta_s,
                "eta_min": eta_s // 60,
            }
        )
    return arrivals


def arrivals_at_stop(stop_id: str, now_s: int | float | None = None, limit: int = 6) -> list[dict]:
    """Arrivals board for one stop: all serving routes merged and sorted by ETA."""
    board = []
    for route_id, route in ROUTES.items():
        if stop_id in route["stops"]:
            board.extend(next_arrivals(route_id, stop_id, now_s, count=3))
    board.sort(key=lambda a: a["eta_seconds"])
    return board[:limit]


def search(origin: str, destination: str, now_s: int | float | None = None) -> list[dict]:
    """Routes that run forward from ``origin`` to ``destination``, fastest journey first."""
    results = []
    for route_id, route in ROUTES.items():
        stops = route["stops"]
        if origin in stops and destination in stops:
            o_idx, d_idx = stops.index(origin), stops.index(destination)
            if o_idx < d_idx:
                ride_min = round(route["trip_min"] * (d_idx - o_idx) / (len(stops) - 1))
                wait_min = next_arrivals(route_id, origin, now_s, count=1)[0]["eta_min"]
                results.append(
                    {
                        "route_id": route_id,
                        "route_name": route["name"],
                        "colour": route["colour"],
                        "wait_min": wait_min,
                        "ride_min": ride_min,
                        "total_min": wait_min + ride_min,
                        "stop_names": [STOPS[s] for s in stops[o_idx : d_idx + 1]],
                    }
                )
    results.sort(key=lambda r: r["total_min"])
    return results


def active_vehicles(now_s: int | float | None = None) -> list[dict]:
    """Simulated vehicles currently in service, with progress 0..1 along their route."""
    now = _now(now_s)
    vehicles = []
    for route_id, route in ROUTES.items():
        headway = route["headway_min"] * 60
        trip = route["trip_min"] * 60
        stops = route["stops"]
        first_k = math.ceil((now - trip) / headway)
        last_k = math.floor(now / headway)
        for k in range(first_k, last_k + 1):
            progress = (now - k * headway) / trip
            if 0 <= progress <= 1:
                position = progress * (len(stops) - 1)
                next_idx = min(len(stops) - 1, int(position) + 1)
                vehicles.append(
                    {
                        "id": f"{route_id}-{k % 1000:03d}",
                        "route_id": route_id,
                        "progress": round(progress, 4),
                        "next_stop": STOPS[stops[next_idx]],
                        "occupancy": OCCUPANCY[k % len(OCCUPANCY)],
                    }
                )
    return vehicles
