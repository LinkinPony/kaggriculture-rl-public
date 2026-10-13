#include "boatlee/detail.hpp"

#include <utility>

namespace kagg::boatlee::detail {

PlayerAction MoonAct(const Portfolio& portfolio, const Engine& engine,
                     int player, MoonState* state) {
  const int step = engine.step_index();
  if (step == 0 || step < state->last_step) *state = MoonState{};
  state->last_step = step;
  ObserveOpponentMarket(portfolio, engine, player, state);
  if (step >= 708) return TerminalAction(engine, player);
  const Tape tape = SelectMoonTape(engine, player, state);
  PlayerAction action = portfolio.action(tape, step);
  action = ApplyWeedRepair(portfolio, engine, player, tape,
                           std::move(action), &state->repair);
  action = ApplyRoomEvac(engine, player, std::move(action), &state->room);
  action = RepayShift(engine, std::move(action), &state->shift);
  action = RankSellSlots(engine, std::move(action));
  action = ApplyPreemptShift(portfolio, engine, player, tape,
                             std::move(action), state);
  action = ApplyR5Counter(portfolio, engine, player, std::move(action),
                          &state->r5);
  action = ApplyMdCounter(portfolio, engine, player, std::move(action),
                          &state->md);
  action = ApplyTomatoPair(engine, player, std::move(action),
                           &state->tomato);
  action = ApplyEggPair(engine, player, std::move(action), &state->egg);
  action = ApplyRoomGuard(engine, player, std::move(action));
  AlignHands(engine, player, &action);
  if (action.market.size() > kMaximumOrders) {
    action.market.resize(kMaximumOrders);
  }
  RecordOwnSells(engine, player, action, &state->race);
  return action;
}

}  // namespace kagg::boatlee::detail
