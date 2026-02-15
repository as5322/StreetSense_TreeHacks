from dataclasses import dataclass
from typing import List


@dataclass
class MonitoredLocation:
    name: str
    city: str
    lat: float
    long: float
    keywords: List[str] | None = None


MONITORED_LOCATIONS: List[MonitoredLocation] = [
    MonitoredLocation(
        name="Oxford Street",
        city="London",
        lat=51.5154,
        long=-0.1410,
    ),
    MonitoredLocation(
        name="Camden Town",
        city="London",
        lat=51.5390,
        long=-0.1426,
    ),
    MonitoredLocation(
        name="Stratford",
        city="London",
        lat=51.5413,
        long=-0.0030,
    ),
    MonitoredLocation(
        name="King's Cross",
        city="London",
        lat=51.5308,
        long=-0.1238,
    ),
]
