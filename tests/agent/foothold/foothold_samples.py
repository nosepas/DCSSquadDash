"""Synthetic persistence files written in Foothold's serialization style (no real server data)."""
# ruff: noqa: E501
from __future__ import annotations

from pathlib import Path

ZONES = """zonePersistance = {}
zonePersistance['zones'] = {
    ['Alpha']={ ['upgradesUsed']=2,['side']=2,['active']=true,['destroyed']={ [1]='x',[2]='y' },['extraUpgrade']={ },['remainingUnits']={ [1]={ [1]='Soldier M4 GRG',[2]='M-2 Bradley' },[2]={ [1]='SA-6' },[3]={ } },['wasBlue']=true,['lat_long']={ ['longitude']=40.572,['latitude']=43.118,['altitude']=12.5 },['firstCaptureByRed']=false,['level']=3,['logisticCenter']=true,['upgradesUsedRed']=0,['upgradesUsedBlue']=2,['triggers']={ ['missioncompleted']=3 } },
    ['Bravo']={ ['upgradesUsed']=0,['side']=1,['active']=true,['destroyed']={ },['extraUpgrade']={ },['remainingUnits']={ },['lat_long']={ ['longitude']=41.0,['latitude']=42.5,['altitude']=0 },['firstCaptureByRed']=true,['level']=1,['triggers']={ } },
    ['Charlie']={ ['side']=0,['active']=false,['level']=0,['lat_long']={ ['longitude']=999,['latitude']=42.5 },['someNewKey']=7 },
    ['Delta']={ ['side']=2,['active']=true,['level']=1,['lat_long']={ ['longitude']=41.5,['latitude']=42.0,['altitude']=0 } }
}
zonePersistance['zonesDetails'] = { ['Alpha']={ ['flavorText']='WPT 8',['hidden']=false }, ['Bravo']={ ['hidden']=true } }
"""

LEGACY_STATS = """zonePersistance['playerStats'] = { ['Mitch']={ ['Points']=2582.5,['Deaths']=2,['Air']=2,['Ground Units']=6,['Flight time']=46 }, ['Bad']=5 }
"""

IDENTITY_STATS = """zonePersistance['playerStatsIdentityVersion'] = 1
zonePersistance['playerStats'] = {
    ['id-aaa']={ ['name']='Mitch',['stats']={ ['Points']=10,['Deaths']=1 } },
    ['id-bbb']={ ['name']='  ',['stats']={ ['Points']=3 } },
    ['id-ccc']={ ['stats']={ } }
}
"""

REST = """zonePersistance['ejectedPilots'] = { [1]={ ['playerName']='Unknown',['latitude']=43.29,['longitude']=40.28,['altitude']=481.08,['lostCredits']=50 }, [2]={ ['latitude']=100,['longitude']=0 } }
zonePersistance['missions'] = { [1]={ ['title']='Intercept Bombers',['description']='Bombers north',['isEscortMission']=false,['isRunning']=true }, [2]={ ['title']='CAS',['isRunning']=false }, [3]={ } }
zonePersistance['connections'] = { [1]={ ['from']='Alpha',['to']='Bravo' }, [2]={ ['from']='Bravo',['to']='Charlie' }, [3]={ ['from']='Alpha' } }
zonePersistance['players'] = { [1]={ ['coalition']='blue',['unitType']='F-16C_50',['playerName']='APOLLO | Tomy10',['latitude']=43.484,['longitude']=40.146,['altitude']=5326.43 }, [2]={ ['playerName']='NoPos' } }
zonePersistance['accounts'] = {
    [1]=0,
    [2]=14524.5,
}
zonePersistance['shops'] = { [1]={ }, [2]={ ['dynamictexaco']={ ['stock']=1 } } }
zonePersistance['tankers'] = { ['texaco']={ ['heading']=45,['leg']=0,['speed']=286,['unlocked']=false } }
zonePersistance['customFlags'] = { [1]=true, ['kutaisicaptured']=true }
zonePersistance['ewrsSettings'] = { }
zonePersistance['difficultyModifier'] = 0
"""


def full_file(stats: str = LEGACY_STATS, extra: str = "") -> str:
    return ZONES + stats + REST + extra


def write_saves(tmp_path: Path, text: str, name: str = "Foothold_Caucasus.lua") -> Path:
    saves = tmp_path / "Saves"
    saves.mkdir(exist_ok=True)
    (saves / name).write_text(text, "utf-8")
    return saves / name
