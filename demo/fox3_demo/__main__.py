"""Local demo: central + simulated agent in one process. Run: python -m fox3_demo [--port 8000]."""
from __future__ import annotations

import argparse
import logging
import threading
import time
from pathlib import Path

import uvicorn

from fox3_agent.sim.data import PILOTS
from fox3_agent.sim.runner import SimAgent
from fox3_agent.sim.scenarios import SCENARIOS, Scenario
from fox3_central.app import create_app
from fox3_central.config import Settings
from fox3_central.repositories import players, servers, users
from fox3_central.services import agents as agent_service


def _server_for(ctx, scenario: Scenario) -> dict:
    """The demo has three servers: two Foothold maps and a training server that is not Foothold."""
    with ctx.tx() as cn:
        found = next((x for x in servers.list_all(cn) if x["name"] == scenario.server_name), None)
        return found or servers.create(cn, scenario.server_name, scenario.mission_type)


def main() -> None:
    ap = argparse.ArgumentParser(description="FOX3 local demo")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--data-dir", type=Path, default=Path("demo-data"))
    ap.add_argument("--tick", type=float, default=2.0, help="seconds between simulated updates")
    ap.add_argument("--reset", action="store_true", help="delete previous demo data first")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    args.data_dir.mkdir(parents=True, exist_ok=True)
    db_file = args.data_dir / "demo.sqlite"
    if args.reset and db_file.exists():
        db_file.unlink()
    settings = Settings(db_url=f"sqlite:///{db_file.as_posix()}", public_base_url=f"http://localhost:{args.port}", demo_login=True)
    app = create_app(settings)
    ctx = app.state.ctx

    scenarios = list(SCENARIOS.values())
    codes = {sc.key: agent_service.create_pairing_code(ctx, _server_for(ctx, sc)["server_id"])["pairing_code"] for sc in scenarios}
    with ctx.tx() as cn:  # the demo pilot flies as the first simulated pilot, so "my side" works out of the box
        demo_user = users.upsert_discord(cn, "demo-user", "Demo Pilot", None, "user")
        players.touch(cn, PILOTS[0][1], PILOTS[0][0])
        players.link(cn, PILOTS[0][1], demo_user["user_id"])

    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning"))
    threading.Thread(target=srv.run, daemon=True).start()
    while not srv.started:
        time.sleep(0.1)

    agents = [SimAgent(f"http://localhost:{args.port}", codes[sc.key], args.data_dir / f"agent-{sc.key}", tick_s=args.tick, scenario=sc)
              for sc in scenarios]
    for agent in agents:
        agent.warmup(150)
        agent.start()
    print(f"\nFOX3 demo running: http://localhost:{args.port}   (Ctrl+C to stop)\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for agent in agents:
            agent.stop()
        srv.should_exit = True


if __name__ == "__main__":
    main()
