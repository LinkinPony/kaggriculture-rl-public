"""Frozen source identities for the September public opponent population."""

from dataclasses import dataclass
from typing import Literal

ActiveAgentId = Literal[
    "ahmed_v45",
    "metacounter_r1",
    "shop_router_0913",
    "rayk_v38_low_pressure",
    "farming_v4_0914",
    "ahmed_v53",
    "thomas_metav4",
]
RetiredAgentId = Literal[
    "ahmed_v42",
    "ahmed_v41",
    "farming_v4_0912",
    "router_95",
    "farming_v4",
    "kaito_v58",
    "shop_router_0908",
    "shop_router_0909",
    "boatlee_v29",
]


@dataclass(frozen=True)
class Source:
    """Bind a public strategy to its exact reviewed source bytes."""

    agent_id: str
    notebook_ref: str
    sha256: str
    files: tuple[tuple[str, str], ...] = ()
    entrypoint: str = "agent"


LEGACY_SOURCES = (
    Source(
        "router_95",
        "thomastschinkel/kaggriculture-95-5-win-rate-via-replay-routing",
        "8241246765098c50223d897739cb32076b71a303284d2e5e1c5f0fb495bb5a97",
    ),
    Source(
        "farming_v4",
        "lynnsakurai/farming-score-v4-a-better-shop",
        "1590394cf30c8989a3e1cfdb027d89b5ccd97c2fb4cdc14959a15555b2b2361a",
    ),
    Source(
        "kaito_v58",
        "kaitofukami/238-238-known-streams-v58-minimax-closed-loop",
        "b041058ec187a8d0a01edc0eab8de068b53deca3e6c1973faf74ace6916ddcb9",
    ),
    Source(
        "shop_router_0908",
        "yhay81/shop-router-0908",
        "66585d1a5dbfe11c946a3c400278592f860342bc4a8f5e5f87f2a9293348984b",
        (
            ("actions.json", "171c8550addac9fdb49acb44af36f64b4eb54e34c561eb6f3d4a83e2dcc803a6"),
            ("model.json", "e6a3a8eff5d499a1764001943c9989bfe5a8ed3da8a5ab457d53012c56f9a378"),
            ("observation.py", "516aee86ca84550839ecc5217cff3464c896a6a69d338f91f7ccfa16fee73fa9"),
        ),
    ),
    Source(
        "shop_router_0909",
        "yhay81/shop-router-0909",
        "d6d74997dc5b483db63d8e39cafa1afeec0f366824e75107e109123f111e866b",
        (
            ("actions.json", "17d503f2fd20d59f9c0f14024d1e74a8add8bb9b5561d4d908b45deecb5495ef"),
            ("LICENSE.txt", "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"),
        ),
    ),
)
SOURCES = (
    Source(
        "ahmed_v45",
        "ahmedberatozer/kaggriculture-v45-first-turn-wheat-round-trip",
        "2536d41ed5a00c75204b6350f1c76c54259c774cb065ba2a3a0072eedf210d94",
    ),
    Source(
        "metacounter_r1",
        "alperen5252525/kaggriculture-metacounter-r1-scored-agent",
        "75e1424c2d560e5e5bf102ab02cf8233d360622bcf086a1811aff839a17067b9",
    ),
    Source(
        "shop_router_0913",
        "yhay81/shop-router-0913",
        "77cf67723a753be957cf70fdb8abbce7ef5c020299e8acd16ed8d2dc8b929dfa",
    ),
    Source(
        "rayk_v38_low_pressure",
        "raykkretzschmar/kaggriculture-rank-your-agent",
        "8f03b16618586e1d9a55c38d5232ea61729b82cdc5abcf383cca73227d4875b5",
        (("my_agent.py", "114123d17ad08ebb71487b885f0f48ae97251b1f9b4495082ea2d799785ddb1c"),),
    ),
    Source(
        "farming_v4_0914",
        "lynnsakurai/farming-score-v4-a-better-shop",
        "03e263f1a20db29d6aa3404e978b97549bdac7f81d2b7f8dea5b36a3d6e91edc",
    ),
    Source(
        "ahmed_v53",
        "ahmedberatozer/kaggriculture-v53-opening-signature",
        "20fe549dd4573b9fd1dfb32a1782c205fa74f0edfdfd6cbe935079533e0a9d0e",
        entrypoint="last_callable",
    ),
    Source(
        "thomas_metav4",
        "thomastschinkel/the-metav4-farm-submission-v13",
        "9d63494603f88219857a3101d7dc19cc750ded04e5886732ee428580326967d9",
    ),
)
ACTIVE_IDS = tuple(source.agent_id for source in SOURCES)
