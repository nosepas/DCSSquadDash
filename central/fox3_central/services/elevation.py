"""Ground elevation lookup for points clicked on the DTC map. Approximate (90 m DEM, not the DCS terrain): the UI keeps it editable."""
from __future__ import annotations

import logging
from collections import OrderedDict

import httpx

log = logging.getLogger("fox3.elevation")
BATCH = 100


class ElevationClient:
    def __init__(self, url: str, timeout_s: float = 6.0, cache_size: int = 5000, transport: httpx.BaseTransport | None = None):
        self._url = url.strip()
        self._http = httpx.Client(timeout=timeout_s, transport=transport)
        self._cache: OrderedDict[tuple[float, float], float] = OrderedDict()
        self._max = cache_size

    @property
    def enabled(self) -> bool:
        return bool(self._url)

    @staticmethod
    def _key(lat: float, lon: float) -> tuple[float, float]:
        return round(lat, 4), round(lon, 4)  # ~11 m: well below the 90 m resolution

    def lookup(self, points: list[tuple[float, float]]) -> list[float | None]:
        """Elevation in metres for each point, None where unknown (service disabled/unreachable)."""
        if not self.enabled:
            return [None] * len(points)
        keys = [self._key(*p) for p in points]
        missing = [k for k in dict.fromkeys(keys) if k not in self._cache]
        for i in range(0, len(missing), BATCH):
            self._fetch(missing[i:i + BATCH])
        return [self._cache.get(k) for k in keys]

    def _fetch(self, batch: list[tuple[float, float]]) -> None:
        try:
            r = self._http.get(self._url, params={"latitude": ",".join(str(k[0]) for k in batch),
                                                  "longitude": ",".join(str(k[1]) for k in batch)})
            r.raise_for_status()
            values = r.json()["elevation"]
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            log.warning("elevation service failed (%s)", type(exc).__name__)
            return
        for key, v in zip(batch, values, strict=False):
            if isinstance(v, (int, float)):
                self._cache[key] = float(v)
                self._cache.move_to_end(key)
        while len(self._cache) > self._max:
            self._cache.popitem(last=False)
