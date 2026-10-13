"""Native observation feature geometry, independent of a training workflow."""

from dataclasses import dataclass

from kagg_revue.native import _revue_core as native
from kagg_revue.policy.settings import GeometrySettings


@dataclass(frozen=True)
class Layout:
    """Resolved tensor layout stored verbatim with each checkpoint."""

    board_features: int
    unit_features: int
    global_features: int
    units: int
    markets: int
    turns: int
    quantities: tuple[int, ...]
    width: int
    version: str
    extra_features: int = 0
    product_features: int = 0
    history_features: int = 0
    support_features: int = 0
    context_features: int = 0
    agronomy_board_features: int = 0
    agronomy_product_features: int = 0
    agronomy_global_features: int = 0
    agronomy_unit_features: int = 0
    derived_global_features: int = 0
    derived_board_features: int = 0
    derived_unit_features: int = 0
    derived_product_features: int = 0

    def __post_init__(self) -> None:
        """Canonicalize sequence identity after JSON or checkpoint deserialization."""
        object.__setattr__(self, "quantities", tuple(self.quantities))

    @property
    def slots(self) -> int:
        """Return parallel output roles."""
        return self.units + self.markets

    @property
    def derived_features(self) -> int:
        """Return the supplement inserted immediately before unit legality support."""
        cells = self.board_features // 58
        return (
            self.derived_global_features
            + 2 * cells * self.derived_board_features
            + 2 * self.units * self.derived_unit_features
            + 9 * self.derived_product_features
        )

    @property
    def features(self) -> int:
        """Return the packed observation width."""
        return (
            self.board_features
            + self.units * self.unit_features
            + self.global_features
            + self.extra_features
            + self.support_features
            + self.context_features
            + self.derived_features
        )

    @classmethod
    def resolve(cls, settings: GeometrySettings) -> "Layout":
        """Derive dimensions from the native ABI and resolved experiment."""
        spec = native.parallel_spec()
        grounded = settings.model.architecture in {"grounded-v1", "grounded-v2"}
        entities = settings.model.architecture in {
            "entities-v2",
            "work-v1",
            "grounded-v1",
            "grounded-v2",
        }
        agronomy = {
            key: int(spec[f"agronomy_{key}_features"]) if settings.model.agronomy else 0
            for key in ("board", "product", "global", "unit")
        }
        product = int(spec["product_features"]) if entities else 0
        history = int(spec["history_features"]) if entities else 0
        return cls(
            2 * int(spec["board_channels"]) * int(settings.environment["boardSize"]) ** 2,
            int(spec["unit_features"]),
            int(spec["global_features"]),
            settings.unit_limit,
            int(settings.environment["maxMarketOrdersPerTurn"]),
            settings.turns,
            settings.quantities,
            settings.width,
            str(
                spec["derived_version"]
                if settings.model.derived
                else spec["agronomy_version"]
                if settings.model.agronomy
                else spec["context_version"]
                if settings.model.architecture == "grounded-v2"
                else spec["grounded_version"]
                if grounded
                else spec["entity_version"]
                if entities
                else spec["version"]
            ),
            settings.unit_limit * int(spec["unit_features"]) + 9 * product + history
            if entities
            else 0,
            product,
            history,
            settings.unit_limit * int(spec["unit_support_features"]) if grounded else 0,
            (
                2
                * int(settings.environment["boardSize"]) ** 2
                * (int(spec["context_board_channels"]) + agronomy["board"])
                + 9 * (int(spec["context_product_features"]) + agronomy["product"])
                + int(spec["context_global_features"])
                + int(spec["context_history_tokens"]) * int(spec["context_history_features"])
                + agronomy["global"]
                + 2 * settings.unit_limit * agronomy["unit"]
            )
            if settings.model.architecture == "grounded-v2"
            else 0,
            agronomy["board"],
            agronomy["product"],
            agronomy["global"],
            agronomy["unit"],
            int(spec["derived_global_features"]) if settings.model.derived else 0,
            int(spec["derived_board_features"]) if settings.model.derived else 0,
            int(spec["derived_unit_features"]) if settings.model.derived else 0,
            int(spec["derived_product_features"]) if settings.model.derived else 0,
        )
