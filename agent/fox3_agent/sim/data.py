"""Fictional demo data on the Caucasus map. Airbase coordinates are approximate and for DEMO only."""
from __future__ import annotations

# name, lat, lon, initial coalition, is_hq
ZONES = [
    ("Anapa", 44.896, 37.316, "red", False), ("Novorossiysk", 44.672, 37.787, "red", False),
    ("Gelendzhik", 44.567, 38.012, "red", False), ("Krymsk", 44.961, 37.987, "red", False),
    ("Krasnodar", 45.085, 38.925, "red", True), ("Maykop", 44.676, 40.021, "red", False),
    ("Sochi", 43.450, 39.940, "neutral", False), ("Gudauta", 43.101, 40.581, "neutral", False),
    ("Sukhumi", 42.858, 41.128, "neutral", False), ("Senaki", 42.241, 42.066, "blue", False),
    ("Kobuleti", 41.930, 41.860, "blue", False), ("Batumi", 41.610, 41.600, "blue", True),
    ("Kutaisi", 42.176, 42.480, "blue", False), ("Mineralnye Vody", 44.225, 43.082, "neutral", False),
    ("Nalchik", 43.510, 43.636, "neutral", False), ("Tbilisi", 41.669, 44.954, "blue", False),
]
CONNECTIONS = [
    ("Anapa", "Novorossiysk"), ("Novorossiysk", "Gelendzhik"), ("Anapa", "Krymsk"), ("Krymsk", "Krasnodar"),
    ("Krasnodar", "Maykop"), ("Gelendzhik", "Sochi"), ("Sochi", "Gudauta"), ("Gudauta", "Sukhumi"),
    ("Sukhumi", "Senaki"), ("Senaki", "Kobuleti"), ("Kobuleti", "Batumi"), ("Senaki", "Kutaisi"),
    ("Maykop", "Nalchik"), ("Nalchik", "Mineralnye Vody"), ("Kutaisi", "Tbilisi"), ("Nalchik", "Kutaisi"),
]
PILOTS = [  # fictional pilots: name, ucid
    ("Viper01", "a1f3c9d0b2e44d7f9c1a000000000001"), ("Maverick", "a1f3c9d0b2e44d7f9c1a000000000002"),
    ("Goose", "a1f3c9d0b2e44d7f9c1a000000000003"), ("Iceman", "a1f3c9d0b2e44d7f9c1a000000000004"),
    ("Jester", "a1f3c9d0b2e44d7f9c1a000000000005"), ("Hollywood", "a1f3c9d0b2e44d7f9c1a000000000006"),
    ("Slider", "a1f3c9d0b2e44d7f9c1a000000000007"), ("Cougar", "a1f3c9d0b2e44d7f9c1a000000000008"),
    ("Merlin", "a1f3c9d0b2e44d7f9c1a000000000009"), ("Stinger", "a1f3c9d0b2e44d7f9c1a00000000000a"),
]
AIRCRAFT = {"blue": ["F-16C_50", "FA-18C_hornet", "F-14B", "AH-64D_BLK_II"], "red": ["Su-27", "MiG-29S", "Su-25T", "MiG-21Bis"]}
AI_TARGETS = ["T-72B", "BMP-2", "ZSU-23-4", "Su-25", "SA-6 Kub", "Ural-375", "S-300 TR"]
WEAPONS = ["AIM-120C", "AIM-9M", "AGM-65D", "GBU-12", "M61A1", "R-27R", "R-73"]
