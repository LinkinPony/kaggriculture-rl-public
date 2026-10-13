"""Hydra command for the intent-ledger oracle language audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.intents.audit import audit_oracle_language
from kagg_revue.rl.intents.audit_config import IntentOracleAuditAppSettings


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> IntentOracleAuditAppSettings:
    """Compose and validate the tracked audit profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="intent_ledger_oracle_audit_config", overrides=overrides)
    payload = OmegaConf.to_container(composed, resolve=True)
    return IntentOracleAuditAppSettings.model_validate(cast(dict[str, Any], payload))


def main() -> None:
    """Run the authenticated Rank8 trace and canonical language audit."""
    settings = load_settings(sys.argv[1:]).intent_ledger_oracle_audit
    report = audit_oracle_language(settings, repository_root())
    print(json.dumps(report, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
