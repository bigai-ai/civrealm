from civrealm.freeciv.utils.freeciv_logging import ray_logger_setup
from civrealm.envs.freeciv_parallel_env import FreecivParallelEnv
from civrealm.configs import fc_args
import ray
import random

class ParallelRunner:
    def __init__(self, env_name, agent):
        # Start ray process
        ray.init(local_mode=False, runtime_env={
                 "worker_process_setup_hook": ray_logger_setup})
        self.logger = ray_logger_setup()

        self.agent = agent
        # Number of envs that run simultaneously
        self.batch_size_run = fc_args['batch_size_run']

        # Initialize envs
        self.envs = []
        for _ in range(self.batch_size_run):
            env = FreecivParallelEnv.remote(env_name)
            self.envs.append(env)

        self.t = 0
        self.batchs = []

    def close(self):
        ray.shutdown()

    def reset(self):
        self.batchs = []
        observations = []
        infos = []
        rewards = [0]*self.batch_size_run
        dones = [False]*self.batch_size_run

        # Reset the envs
        result_ids = [self.envs[i].reset.remote()
                      for i in range(self.batch_size_run)]
        results = ray.get(result_ids)

        for i in range(self.batch_size_run):
            observations.append(results[i][0])
            infos.append(results[i][1])

        self.batchs.append((observations, infos, rewards, dones))

        self.t = 0
        self.env_steps_this_run = 0

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
            # Make decision and send action for each parallel environment
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
