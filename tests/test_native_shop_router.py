from pathlib import Path

from kagg_revue.native import _revue_native as native
from kagg_revue.opponents.native_batch import create_native_opponent_session
from kagg_revue.opponents.public import PublicAgentRuntime, load_public_agent_manifest


def test_frozen_router_boundaries_repeated_calls_clones_and_episode_reset():
    manifest = Path("data/external/kaggriculture-shop-router-0908-20260908/manifest.json")
    record = load_public_agent_manifest(manifest).by_id()["shop_router_0908"]
    decisions = set()
    session = create_native_opponent_session("shop_router_0908", 10)
    # Exercise exact threshold equality and both adjacent integer stocks. The
    # large sale intervals keep the chosen stock constant after initialization.
    for seed in (1860908110, 1860908123):
        config = {"townShopSellInterval": 10000, "townCenterSellInterval": 10000}
        baseline = native.Engine(seed, config)
        for _ in range(648):
            baseline.step({}, {})
        initial_stock = baseline.observation(0)["market"]["inventory"]["EGG"]
        for stock in (9887, 9888, 9889):
            engine = native.Engine(
                seed, {**config, "marketParams": {"EGG": {"I0": stock + 10000 - initial_stock}}}
            )
            original = PublicAgentRuntime(record, Path.cwd(), engine.configuration)
            fork = None
            for turn in range(719):
                observation = engine.observation(0)
                expected = native.canonical_opponent_action(original.act(observation), 10)
                actual = native.native_opponent_action(engine, 0, session)
                assert native.canonical_opponent_action(actual, 10) == expected
                if fork is not None:
                    copied = native.native_opponent_action(engine, 0, fork)
                    assert native.canonical_opponent_action(copied, 10) == expected
                if turn in (143, 647):
                    fork = session.clone()
                if turn in (144, 648):
                    repeated = native.native_opponent_action(engine, 0, session)
                    assert native.canonical_opponent_action(repeated, 10) == expected
                    decision = original._function.__globals__["_ROUTER"].decisions[-1]
                    decisions.add((turn, decision["choice"]))
                    if turn == 648:
                        assert decision["features"][71] == stock
                        assert decision["choice"] == (2 if stock <= 9888 else 3)
                engine.step({}, {})
    assert decisions == {(144, 0), (144, 1), (648, 2), (648, 3)}


def test_0909_all_ordered_shop_pairs_daily_queues_sales_clones_and_resets():
    manifest = Path("data/external/kaggriculture-shop-router-0909-20260909/manifest.json")
    record = load_public_agent_manifest(manifest).by_id()["shop_router_0909"]
    seeds = {}
    for seed in range(1860909500, 1860911500):
        engine = native.Engine(seed, {})
        probe = create_native_opponent_session("shop_router_0909", 10)
        for _ in range(144):
            engine.step(native.native_opponent_action(engine, 0, probe), {})
        shops = tuple(engine.observation(0)["town"]["unlocked_shops"][:2])
        seeds.setdefault(shops, seed)
        if len(seeds) == 64:
            break
    assert len(seeds) == 64
    session = create_native_opponent_session("shop_router_0909", 10)
    plans, queued, advanced = set(), False, False
    for seed in seeds.values():
        engine = native.Engine(seed, {})
        original = PublicAgentRuntime(record, Path.cwd(), engine.configuration)
        fork = None
        for step in range(719):
            observation = engine.observation(0)
            expected = native.canonical_opponent_action(original.act(observation), 10)
            actual = native.native_opponent_action(engine, 0, session)
            assert native.canonical_opponent_action(actual, 10) == expected
            if fork is not None:
                copied = native.native_opponent_action(engine, 0, fork)
                assert native.canonical_opponent_action(copied, 10) == expected
            state = original._function.__globals__["_POLICY"].players[0]
            plans.add(state.plan)
            queued |= any(state.queues.values())
            advanced |= bool(state.advanced_sales)
            if step in (143, 167, 647, 717):
                fork = session.clone()
            if step in (145, 649):
                # 0909 deliberately resets on repeated calls, unlike 0908.
                expected = native.canonical_opponent_action(original.act(observation), 10)
                actual = native.native_opponent_action(engine, 0, session)
                assert native.canonical_opponent_action(actual, 10) == expected
                fork = session.clone()
            engine.step(actual, {})
    assert plans == set(range(13))
    assert queued and advanced
