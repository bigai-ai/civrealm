## Initializing a Basic Environment

Initializing a basic/LLM Freeciv environment is simple with the Gymnasium API:

=== "A Basic Enviornment"

    ```python
    import gymnasium
    env = gymnasium.make('freeciv/FreecivBase-v0')
    ```

=== "An LLM Enviornment"

    ```python
    import gymnasium
    from civrealm.envs.freeciv_wrapper import LLMWrapper
    env = gymnasium.make('freeciv/FreecivBase-v0')
    env = LLMWrapper(env)
    ```

## Interacting with the Environment

Interactions can also be implemented in the Gymnasium style:

```python
observations, info = env.reset()
done = False
step = 0
while not done:
    action = agent.act(observations, info)
    observations, reward, terminated, truncated, info = env.step(action)
    print(f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}, action: {action}')
    step += 1
    done = terminated or truncated
env.close()
```

## Plot the Game Results

The game results can be plotted with the following code. The figures can be found under the `plot_game_scores` folder.

```{ .python .select }
env.plot_game_scores()
game_results = env.get_game_results()
print('game results:', game_results)
```

!!! tip "Customize the Environment"
    We provide a set of configurations to customize the environment. For example, you can use the `--max_turns` argument to specify the maximum number of turns in a game. For more details, please refer to the [Game Settings](../advanced_materials/game_setting.md) page.

## Putting Things Together

To combine the above code snippets, we can write a simple script to initialize an (LLM) environment, interact with it using a random (LLM) agent, and plot the game results.

=== "With a Basic Enviornment"

    ```python
    from civrealm.agents import RandomAgent
    import gymnasium

    env = gymnasium.make('freeciv/FreecivBase-v0')
    agent = RandomAgent()

    observations, info = env.reset()
    done = False
    step = 0
    while not done:
        action = agent.act(observations, info)
        observations, reward, terminated, truncated, info = env.step(
            action)
        print(f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}, action: {action}')
        step += 1
        done = terminated or truncated
    env.close()

    env.plot_game_scores()
    game_results = env.get_game_results()
    print('game results:', game_results)
    ```

=== "With an LLM Environment"

    ```python
    from civrealm.envs.freeciv_wrapper import LLMWrapper
    from civrealm.agents import RandomLLMAgent
    import gymnasium

    env = gymnasium.make('freeciv/FreecivBase-v0')
    env = LLMWrapper(env)
    agent = RandomLLMAgent()

    observations, info = env.reset()
    done = False
    step = 0
    while not done:
        action = agent.act(observations, info)
        observations, reward, terminated, truncated, info = env.step(
            action)
        print(f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}, action: {action}')
        step += 1
        done = terminated or truncated
    env.close()

    env.plot_game_scores()
    game_results = env.get_game_results()
    print('game results:', game_results)
    ```
