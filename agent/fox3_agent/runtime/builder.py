"""Build a ready-to-run Agent from the validated local configuration (the rest comes from the admin panel)."""
from __future__ import annotations

from ..client import CentralClient
from ..config import AgentConfig
from ..credentials import CredentialStore
from ..outbox import Outbox
from ..sender import Sender
from .agent import Agent
from .detected import detected_folders
from .source_set import LiveSources
from .state import AgentState
from .transfers import TransferResponder


class NotPairedError(RuntimeError):
    pass


def central_client(cfg: AgentConfig) -> CentralClient:
    creds = CredentialStore(cfg.state_dir, cfg.central.api_key_env).load()
    if creds is None:
        raise NotPairedError("this agent is not paired yet: run `fox3-agent pair --code <code>`")
    verify: bool | str = cfg.central.ca_file or cfg.central.verify_tls
    return CentralClient(cfg.central.url, creds.api_key, verify=verify)


def build_agent(cfg: AgentConfig) -> Agent:
    state = AgentState(cfg.state_dir)
    client = central_client(cfg)
    live = LiveSources(cfg, state)
    outbox = Outbox(cfg.queue_path, cfg.queue.max_messages, cfg.queue.max_bytes)
    iv = cfg.intervals
    return Agent(provider=live, outbox=outbox, sender=Sender(outbox, client), state=state, tick_s=iv.tick_s, heartbeat_s=iv.heartbeat_s,
                 server_info_s=iv.server_info_s, config_fetch=client.get_config, detect=detected_folders,
                 responder=TransferResponder(client, lambda: live.tacview_folder))
