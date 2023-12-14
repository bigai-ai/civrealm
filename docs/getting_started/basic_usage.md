# Basic Usage

## Initializing an Environment

Initializing a basic/LLM Freeciv environment is simple with the Gymnasium API:

=== "Full Game"

    ```python
    import gymnasium
    env = gymnasium.make('civrealm/FreecivBase-v0')
    ```

=== "Mini-Game"

    ```python
    import gymnasium
    env = gymnasium.make('civrealm/FreecivMinitask-v0')
    ```

!!! note "LLM Environment"
    To make the environment an LLM environment, you can further wrap it with the `LLMWrapper` class. This applies to both the full game and mini-games as well as their tensor versions. Please refer to the [API Reference](../api_reference/environments.md) page for more details about these environments.

    ```python
    from civrealm.envs.freeciv_wrapper import LLMWrapper
    env = LLMWrapper(env)
    ```

## Interacting with the Environment

Interactions can also be implemented in the Gymnasium style:

```python
from civrealm.agents import RandomAgent
agent = RandomAgent()

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

!!! note "LLM Random Agent"

    You can use `RandomLLMAgent` to test the LLM environment.

    ```python
    from civrealm.agents import RandomLLMAgent
    agent = RandomLLMAgent()
    ```

## Plot the Game Results

The game results can be plotted with the following code. The figures can be found under the `plot_game_scores` folder.

```{ .python .select }
env.plot_game_scores()
game_results = env.get_game_results()
print('game results:', game_results)
```

!!! success
    Now, if we run the script, we should see outputs similar to the command `test_civrealm`:

    ```bash
    Reset with port: 6300
    Step: 0, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 102, 'build_city')
    Step: 1, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 109, 'goto_6')
    Step: 2, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 110, 'goto_0')
    Step: 3, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 111, 'goto_1')
    Step: 4, Turn: 1, Reward: 0, Terminated: False, Truncated: False, action: ('unit', 112, 'goto_5')
    ```

!!! tip "Customize the Environment"
    We provide a set of configurations to customize the environment. For example, you can use the `--max_turns` argument to specify the maximum number of turns in a game. For more details, please refer to the [Game Settings](../advanced_materials/game_settings.md) page.

## Putting Things Together

To combine the above code snippets, we can write a simple script to initialize an (LLM) environment, interact with it using a random (LLM) agent, and plot the game results.

=== "With a Base Enviornment"

    ```python
    from civrealm.agents import RandomAgent
    import gymnasium

    env = gymnasium.make('civrealm/FreecivBase-v0')
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

    env = gymnasium.make('civrealm/FreecivBase-v0')
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
