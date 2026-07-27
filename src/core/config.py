"""Loads config.yaml and merges in environment variables (.env)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Load config.yaml once and cache it for the process lifetime."""
    config_path = PROJECT_ROOT / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_env(var_name: str, required: bool = True) -> str:
    """Fetch an environment variable, raising a clear error if a required one is missing."""
    value = os.getenv(var_name)
    if required and not value:
        raise RuntimeError(
            f"Missing required environment variable: {var_name}. "
            f"Copy .env.example to .env and fill in real values."
        )
    return value or ""


def agent_config(agent_name: str) -> dict:
    """Convenience accessor for a single agent's config block."""
    cfg = get_config()
    agents = cfg.get("agents", {})
    if agent_name not in agents:
        raise KeyError(f"No config found for agent '{agent_name}'. Check config.yaml.")
    return agents[agent_name]
