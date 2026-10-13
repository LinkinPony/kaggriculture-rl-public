"""Experimental public-observation market controllers around a frozen route."""

from typing import Any

from kagg_revue.opponents.research.settings import Variant

_INPUTS = {"WHEAT", "FERTILIZER"}


def apply_market(
    observation: dict[str, Any],
    action: dict[str, Any],
    namespace: dict[str, Any],
    variant: Variant,
    counters: dict[str, int],
) -> dict[str, Any]:
    """Advance eligible sales using only own inventory and the own route plan."""
    step = int(observation["step"])
    if variant.market == "parent" or not variant.sale_start <= step <= variant.sale_end:
        return action
    view = namespace["FarmView"](observation)
    stock = namespace["projected_shed"](action, view)
    orders = [list(order) for order in action.get("market", [])]
    if variant.market == "priority":
        return _priority(observation, action, orders, stock, namespace, counters)
    native = namespace["_IMPL"].chassis.players[int(observation["player"])]
    commands = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    blocked = {command[1] for command in commands if len(command) > 1 and command[0] == "PICKUP"}
    blocked.update(
        command[1]
        for queue in native["pending"].values()
        for _, command in queue
        if len(command) > 1 and command[0] == "PICKUP"
    )
    blocked.update(order[1] for order in orders if len(order) > 1)
    debts = native["sell_state"].setdefault("r36_debts", {})
    tape = namespace["_IMPL"].chassis.routes[native["route"]]
    for item, held in stock.items():
        if item in _INPUTS or item in blocked or held <= 0 or len(orders) >= 10:
            continue
        if observation["market"]["prices"].get(item, 0) < variant.minimum_price:
            continue
        quantity = int(held)
        reservations: list[tuple[int, int]] = []
        if variant.market == "lead":
            available = quantity
            end = min(variant.sale_end, step + variant.lead, (step // 72 + 1) * 72 - 1)
            for due in range(step + 1, end + 1):
                future = tape[due]
                units = [future.get("farmer", ["PASS"]), *future.get("hands", [])]
                if any(command[:2] == ["PICKUP", item] for command in units):
                    break
                planned = sum(
                    int(order[2])
                    for order in future.get("market", [])
                    if len(order) >= 3 and order[:2] == ["SELL", item]
                )
                amount = min(available, max(0, planned - debts.get(due, {}).get(item, 0)))
                if amount:
                    reservations.append((due, amount))
                    available -= amount
                if not available:
                    break
            quantity = sum(amount for _, amount in reservations)
        if not quantity:
            continue
        orders.append(["SELL", item, quantity])
        counters["advanced_units"] = counters.get("advanced_units", 0) + quantity
        for due, amount in reservations:
            debt = debts.setdefault(due, {})
            debt[item] = debt.get(item, 0) + amount
    if orders != action.get("market", []):
        counters["market_changes"] = counters.get("market_changes", 0) + 1
    if variant.priority:
        return _priority(observation, action, orders, stock, namespace, counters)
    return dict(action, market=orders)


def _priority(
    observation: dict[str, Any],
    action: dict[str, Any],
    orders: list[list[Any]],
    stock: dict[str, int],
    namespace: dict[str, Any],
    counters: dict[str, int],
) -> dict[str, Any]:
    """Remove ineffective sells and prioritize price exposure within sale blocks."""
    projected = dict(stock)
    filtered: list[list[Any]] = []
    for order in orders:
        if not order:
            continue
        if len(order) >= 3 and order[0] == "SELL":
            quantity = min(int(order[2]), projected.get(order[1], 0))
            if quantity <= 0:
                continue
            projected[order[1]] -= quantity
        elif len(order) >= 3 and order[0] == "BUY_PRODUCT":
            projected[order[1]] = projected.get(order[1], 0) + int(order[2])
        filtered.append(order)
    index = 0
    while index < len(filtered):
        if filtered[index][0] != "SELL":
            index += 1
            continue
        end = index
        while end < len(filtered) and filtered[end][0] == "SELL":
            end += 1
        filtered[index:end] = sorted(
            filtered[index:end],
            key=lambda order: namespace["_r37_quote_priority"](observation, order, stock),
            reverse=True,
        )
        index = end
    if filtered != orders:
        counters["priority_changes"] = counters.get("priority_changes", 0) + 1
    return dict(action, market=filtered)
