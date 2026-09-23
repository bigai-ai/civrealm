"""A pact clause the other side put on the table can be accepted.

`AddClause.is_clause_valid` refuses a pact clause whose giver is the counterpart, so that the
add-clause action space lists each pact once. `AcceptTreaty` reused that check on the clauses
already in the meeting, so every ceasefire or peace an AI proposed was reported as never
acceptable. No server needed: the check reads only the dicts below."""
import civrealm.freeciv.players.player_const as player_const
from civrealm.freeciv.players.diplomacy_actions import AcceptTreaty


def _accept(giver, ds=player_const.DS_WAR, clause_type=player_const.CLAUSE_CEASEFIRE):
    me = {'playerno': 0, 'team': 0, 'real_embassy': [1, 1]}
    them = {'playerno': 1, 'team': 1, 'real_embassy': [1, 1]}
    clause_map = {1: [{'counterpart': 1, 'giver': giver, 'type': clause_type, 'value': 0}]}
    return AcceptTreaty(clause_map, [[0, 0], [0, 0]], me, them, None,
                        {1: ds}, {0: {1: ds}, 1: {0: ds}}, {0: me, 1: them}, None)


def test_a_ceasefire_the_counterpart_proposed_can_be_accepted():
    assert _accept(giver=1).is_action_valid()


def test_a_ceasefire_we_proposed_can_be_accepted():
    assert _accept(giver=0).is_action_valid()


def test_a_ceasefire_already_in_force_still_cannot_be_accepted():
    assert not _accept(giver=1, ds=player_const.DS_CEASEFIRE).is_action_valid()
