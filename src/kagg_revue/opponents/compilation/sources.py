"""Exact reviewed source identities for the active public script population."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import Field

from kagg_revue.configuration import FrozenSettings
from kagg_revue.opponents.compilation.normalization import Normalization


class ExtraSource(FrozenSettings):
    """Hash-bound local research source added without changing the default population."""

    path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    normalization: Normalization = "none"


@dataclass(frozen=True)
class Candidate:
    """Bind a public runtime to its new immutable training identity."""

    agent_id: str
    survey_id: str
    sha256: str
    normalization: Normalization = "none"
    entrypoint: str = "agent"


CANDIDATES = (
    Candidate(
        "ahmed_v45",
        "ahmed_v45",
        "2536d41ed5a00c75204b6350f1c76c54259c774cb065ba2a3a0072eedf210d94",
        "v43-container-copy",
    ),
    Candidate(
        "metacounter_r1",
        "metacounter",
        "75e1424c2d560e5e5bf102ab02cf8233d360622bcf086a1811aff839a17067b9",
    ),
    Candidate(
        "shop_router_0913",
        "shop_0913",
        "77cf67723a753be957cf70fdb8abbce7ef5c020299e8acd16ed8d2dc8b929dfa",
    ),
    Candidate(
        "rayk_v38_low_pressure",
        "rank_agent",
        "8f03b16618586e1d9a55c38d5232ea61729b82cdc5abcf383cca73227d4875b5",
    ),
    Candidate(
        "farming_v4_0914",
        "farming_v4_refresh",
        "03e263f1a20db29d6aa3404e978b97549bdac7f81d2b7f8dea5b36a3d6e91edc",
    ),
    Candidate(
        "ahmed_v53",
        "ahmed_v53",
        "20fe549dd4573b9fd1dfb32a1782c205fa74f0edfdfd6cbe935079533e0a9d0e",
        "v43-container-copy",
        "_e363_agent",
    ),
    Candidate(
        "thomas_metav4",
        "thomas_metav4",
        "9d63494603f88219857a3101d7dc19cc750ded04e5886732ee428580326967d9",
    ),
)
