"""Authenticated immutable assets and episode-local native policy sessions."""

import hashlib
import json
import zlib
from functools import cache
from pathlib import Path
from typing import Any

from kagg_revue.opponents.portfolios.catalog import LEGACY_SOURCES, SOURCES

ASSET_SHA256 = {
    "thomas_metav4": "c0de2bc51c686214778dc79dda481c219f309a6a0e90e70ebd23d03e397ca627",
    "ahmed_v53": "3bd2c8da24ea461ae90c5be492c5447ec362acda69af4af2b045a407f37beb24",
    "ahmed_v45": "8330113029b88423ac99d257b9d21dd610c70ce8821b4584b44f12742ee6063e",
    "ahmed_v42": "cb7eeb704b353496259184c5a6c475d0f90fd0ec4579a5c316df4ca44368ea5c",
    "farming_v4_0914": "7c3562faedaf2b3cc028b1468333ed485dfde9c2e630178514ee4f85a2eb9d42",
    "ahmed_v41": "5ab740572fd474cf72346eba8b6e58d7de410768a65d0acd6e1514ebb0edf3b2",
    "metacounter_r1": "c8fd00df38d37cf7f310919f44b56a54cb65166163ac9c61d9a7453edaed8feb",
    "shop_router_0913": "e725b6af93e2c0432d68493b3b66530176aa85786192a8306c110f5f97f4aa82",
    "rayk_v38_low_pressure": "a0689b005f440d269b429e33bcdeeab6543b8c2eca89ae886fc6d8f388b9f67e",
    "farming_v4_0912": "5d31fe8b8d0de7ad781c34cbcb8abe0e729f4b551df16c52896f32a9e3faac33",
    "router_95": "9a7c7d3cc380bab8cb31553db8d00c6b81574a0dc4dd8821519aebd8b17e5c3b",
    "farming_v4": "1db7b742ceac47a4c334bb2884f2df24b2b2e3365edd5d79a2134a1e82906c0e",
    "kaito_v58": "ab3d1c3146545273b8491c72f920e32889699cf81b0012c4aa73281743b4a9ef",
    "shop_router_0908": "6e50029b32ec1f6e48794892c765beca62ad88ac9db9e859b6dd70c0039a629e",
    "shop_router_0909": "eab3ee1ef7e4b2b40830b835fdd785db19e2fdfd7366ec2aa94d5f3e9171f52b",
}


@cache
def _portfolio(agent_id: str) -> Any:
    from kagg_revue.native import _revue_native as native

    source = next(
        (source for source in (*SOURCES, *LEGACY_SOURCES) if source.agent_id == agent_id), None
    )
    if agent_id not in ASSET_SHA256 or source is None:
        raise ValueError(f"inactive native opponent: {agent_id}")
    raw = Path(__file__).with_name(f"{agent_id}.json.zlib").read_bytes()
    if hashlib.sha256(raw).hexdigest() != ASSET_SHA256[agent_id]:
        raise ValueError(f"opponent asset hash mismatch: {agent_id}")
    payload = json.loads(zlib.decompress(raw))
    if payload["agent_id"] != agent_id or payload["source_sha256"] != source.sha256:
        raise ValueError(f"opponent source identity mismatch: {agent_id}")
    if "constants" in payload:
        payload["constants"] = [
            bytes.fromhex(value["__native_bytes__"])
            if isinstance(value, dict) and set(value) == {"__native_bytes__"}
            else value
            for value in payload["constants"]
        ]
    return native.NativeOpponentPortfolio(payload)


def create_native_session(agent_id: str, maximum_market_orders: int = 10) -> Any:
    """Share read-only route assets while allocating private mutable state."""
    from kagg_revue.native import _revue_native as native

    return native.NativeOpponentSession(_portfolio(agent_id), maximum_market_orders)


def native_action(session: Any, engine: Any, player: int) -> dict[str, Any]:
    """Expose direct-engine actions for conformance, outside the training loop."""
    from kagg_revue.native import _revue_native as native

    return native.native_opponent_action(engine, player, session)
