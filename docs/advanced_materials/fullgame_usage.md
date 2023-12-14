# Initialize a Full-Game

By default, an environment specified by `civrealm/FreecivBase-v0` will run the full-game.

```python
from civrealm.agents import ControllerAgent
import gymnasium

env = gymnasium.make('civrealm/FreecivBase-v0')
agent = ControllerAgent()
observations, info = env.reset(client_port=fc_args['client_port'])
done = False
step = 0
while not done:
    try:
        action = agent.act(observations, info)
        observations, reward, terminated, truncated, info = env.step(
            action)
        print(
            f'Step: {step}, Turn: {info["turn"]}, Reward: {reward}, Terminated: {terminated}, '
            f'Truncated: {truncated}, action: {action}')
        step += 1
        done = terminated or truncated
    except Exception as e:
        fc_logger.error(repr(e))
        raise e
env.close()
```
