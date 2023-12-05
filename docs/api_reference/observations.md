# Observation Space

The Gymnasium definition for the observation space. At the root is a `Dict` space with the following keys: `['game', 'rules', 'map', 'player', 'city', 'tech', 'unit', 'options', 'dipl', 'gov', 'client']`. We describe the important state spaces below.

!!! tip "Click on the source code below to show the space definition."

## Map State

::: freeciv.map.map_state.MapState.get_observation_space
    options:
      show_root_heading: false

## City State

::: freeciv.city.city_state.CityState.get_observation_space
    options:
      show_root_heading: false

## Unit State

::: freeciv.units.unit_state.UnitState.get_observation_space
    options:
      show_root_heading: false

## Tech State

::: freeciv.tech.tech_state.TechState.get_observation_space
    options:
      show_root_heading: false

## Player State

::: freeciv.players.player_state.PlayerState.get_observation_space
    options:
      show_root_heading: false

## Diplomatic state

::: freeciv.players.diplomacy_state_ctrl.DiplomacyState.get_observation_space
    options:
      show_root_heading: false
