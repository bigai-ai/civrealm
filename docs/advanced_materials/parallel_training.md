Civrealm supports parallel training to speed up the learning process. Concretely, we use [Ray](https://www.ray.io/) to implement the parallel training function in the `FreecivParallelEnv` class located in `src/civrealm/envs/freeciv_parallel_env.py`. To initialize the parallel running environments, simply create multiple `FreecivParallelEnv`objects:

```python
def __init__(self, env_name, agent):
    # Number of envs that run simultaneously
    self.batch_size_run = fc_args['batch_size_run']
    # Initialize envs
    self.envs = []
    for _ in range(self.batch_size_run):
        env = FreecivParallelEnv.remote(env_name)
        self.envs.append(env)
```

To reset the environments to get initial observations, we can call the reset() method of each `FreecivParallelEnv`object. Each `FreecivParallelEnv`object will run its reset process simultaneously and we can retrieve the results based on the result ids.

```python
def reset(self):
    observations = []
    infos = []
    # Reset the envs
    result_ids = [self.envs[i].reset.remote()
                    for i in range(self.batch_size_run)]
    results = ray.get(result_ids)
    
    for i in range(self.batch_size_run):
        observations.append(results[i][0])
        infos.append(results[i][1])
```

After the environments are reset, we call the step() method of each `FreecivParallelEnv`object to play the game. Similar to reset, each `FreecivParallelEnv`object runs its step process simultaneously and we can retrieve the results based on the result ids. After all parallel running environments are terminated, we call the close() method of `FreecivParallelEnv`objects to close them.

```python
def run(self):
    self.reset()
    all_terminated = False
    # Store whether an env has terminated
    dones = [False]*self.batch_size_run
    # Store whether an env has closed its connection
    closed_envs = [False]*self.batch_size_run

    while True:
        observations = [None] * self.batch_size_run
        infos = [None] * self.batch_size_run
        rewards = [0]*self.batch_size_run
        # Start the parallel running
        result_ids = []
        # key: index of result_ids, value: id of env
        id_env_map = {}
        # Make a decision and send action for each parallel environment
        for i in range(self.batch_size_run):
            if not dones[i]:
                observation = self.batchs[self.t][0][i]
                info = self.batchs[self.t][1][i]
                if random.random() < 0.1:
                    action = None
                else:
                    action = self.agent.act(observation, info)
                print(f"Env ID: {i}, turn: {info['turn']}, action: {action}")
                id = self.envs[i].step.remote(action)
                result_ids.append(id)
                id_env_map[id] = i

        finished = False
        unready = result_ids
        # Get the result of each environment one by one
        while not finished:
            # The num_returns=1 ensures ready length is 1.
            ready, unready = ray.wait(unready, num_returns=1)
            # Get the env id corresponding to the given result id
            env_id = id_env_map[ready[0]]
            try:
                result = ray.get(ready[0])
                observations[env_id] = result[0]
                rewards[env_id] = result[1]
                terminated = result[2]
                truncated = result[3]
                infos[env_id] = result[4]
                dones[env_id] = terminated or truncated
                print(f'Env ID: {env_id}, reward: {rewards[env_id]}, done: {dones[env_id]}')
            except Exception as e:
                print(str(e))
                self.logger.warning(repr(e))
                dones[env_id] = True
            if not unready:
                finished = True
        self.batchs.append(
            (observations, infos, rewards, dones))

        result_ids = []
        # Close the terminated environment
        for i in range(self.batch_size_run):
            if dones[i] and not closed_envs[i]:
                result_ids.append(self.envs[i].close.remote())
                closed_envs[i] = True
        ray.get(result_ids)
        all_terminated = all(dones)
        if all_terminated:
            break
        # Move onto the next timestep
        self.t += 1

    return self.batchs
```

For a complete example, you may refer to the `ParallelRunner` class located in `src/civrealm/runners/parallel_runner.py`. You can run `src/civrealm/random_game_parallel.py` to test `ParallelRunner`. In addition, you can also regard the `ParallelTensorEnv` class located in `src/civrealm/envs/parallel_tensor_env.py` as an example. The `TensorBaselineEnv` class in the `civtensor` package uses the `ParallelTensorEnv` class to achieve parallel training.