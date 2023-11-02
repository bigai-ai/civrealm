import gymnasium
import civrealm
from civrealm.freeciv.utils.freeciv_logging import ray_logger_setup
from civrealm.envs.freeciv_a3c_env import FreecivA3CEnv
from civrealm.configs import fc_args
import ray
import copy


class A3CRunner:
    def __init__(self, env_name, agent, logger, epoch_num):
        ray.init(local_mode=False, runtime_env={"worker_process_setup_hook": ray_logger_setup})
        self.logger = ray_logger_setup()

        # Number of envs that run simultaneously
        self.batch_size_run = fc_args['batch_size_run']
        # self.agent = agent

        # Initialize envs
        self.envs = []

        port_start = fc_args['port_start']
        for i in range(self.batch_size_run):
            temp_port = port_start+epoch_num % 2*self.batch_size_run+i
            env_core = gymnasium.make(env_name, client_port=temp_port)
            env = FreecivA3CEnv.remote(env_core, agent, temp_port)
            self.envs.append(env)

        self.t = 0
        self.t_env = 0

        self.batchs = []
        self.train_returns = []
        self.test_returns = []
        self.train_stats = {}
        self.test_stats = {}

        self.log_train_stats_t = -100000

    def close(self):
        ray.shutdown()

    def reset(self):
        self.batchs = []
        observations = []
        infos = []
        rewards = [0]*self.batch_size_run
        dones = [False]*self.batch_size_run

        # Reset the envs
        result_ids = [self.envs[i].reset.remote() for i in range(self.batch_size_run)]
        results = ray.get(result_ids)
        for i in range(self.batch_size_run):
            observations.append(results[i][0])
            infos.append(results[i][1])

        self.batchs.append((observations, infos, rewards, dones))

        self.t = 0
        self.env_steps_this_run = 0

    def run(self, test_mode=False):
        self.reset()
        episode_returns = [0 for _ in range(self.batch_size_run)]
        episode_lengths = [0 for _ in range(self.batch_size_run)]
        # self.agent.init_hidden(batch_size=self.batch_size_run)

        all_terminated = False
        # Store whether an env has terminated
        dones = [False]*self.batch_size_run
        # Store whether an env has closed its connection
        closed_envs = [False]*self.batch_size_run

        envs_not_terminated = [b_idx for b_idx, done in enumerate(dones) if not done]
        # final_env_infos = []  # may store extra stats like battle won. this is filled in ORDER OF TERMINATION

        while True:
            # Pass the entire batch of experiences up till now to the agents
            # Receive the actions for each agent at this timestep in a batch for each un-terminated env
            # actions = self.agent.select_actions(self.batch, t_ep=self.t, t_env=self.t_env, bs=envs_not_terminated, test_mode=test_mode)

            # # Update the actions taken
            # actions_chosen = {
            #     "actions": actions.unsqueeze(1)
            # }
            # self.batch.update(actions_chosen, bs=envs_not_terminated, ts=self.t, mark_filled=False)

            observations = [None] * self.batch_size_run
            infos = [None] * self.batch_size_run
            rewards = [0]*self.batch_size_run
            # Start the parallel running
            result_ids = []
            # key: index of result_ids, value: id of env
            id_env_map = {}
            for i in range(self.batch_size_run):
                if not dones[i]:
                    observation = self.batchs[self.t][0][i]
                    info = self.batchs[self.t][1][i]
                    # import random
                    # if random.random() < 0.3:
                    #     action = 'pass'
                    # else:
                    #     action = None
                    action = ray.get(self.envs[i].compute_action.remote(observation, info))
                    # print(observation)
                    # print(info)
                    # print(action)
                    id = self.envs[i].step.remote(action)
                    result_ids.append(id)
                    id_env_map[id] = i
                    if not test_mode:
                        self.env_steps_this_run += 1

            # The num_returns=1 ensures ready length is 1.
            ready, unready = ray.wait(result_ids, num_returns=1)
            while unready:
                # Get the env id corresponds to the given result id
                env_id = id_env_map[ready[0]]
                # print(f'env_id: {env_id}')
                try:
                    result = ray.get(ready[0])
                    # print(result)
                    observations[env_id] = result[0]
                    rewards[env_id] = result[1]
                    terminated = result[2]
                    truncated = result[3]
                    infos[env_id] = result[4]
                    dones[env_id] = terminated or truncated
                    # , reward, terminated, truncated, infos[env_id] = result[0], result[1], result[2], result[3],
                except Exception as e:
                    print(str(e))
                    self.logger.warning(repr(e))
                    dones[env_id] = True
                ready, unready = ray.wait(unready, num_returns=1)

            # Handle the last ready result
            if ready:
                env_id = id_env_map[ready[0]]
                # print(f'env_id: {env_id}')
                try:
                    result = ray.get(ready[0])
                    # print(result)
                    observations[env_id] = result[0]
                    rewards[env_id] = result[1]
                    terminated = result[2]
                    truncated = result[3]
                    infos[env_id] = result[4]
                    dones[env_id] = terminated or truncated
                except Exception as e:
                    self.logger.warning(repr(e))
                    dones[env_id] = True

            self.batchs.append((observations, infos, rewards, copy.deepcopy(dones)))
            # print(f'done_list: {done_list}')
            # print(f'observation_list: {observation_list}')

            # Update envs_not_terminated
            envs_not_terminated = [b_idx for b_idx, termed in enumerate(dones) if not termed]

            result_ids = []
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

        if not test_mode:
            self.t_env += self.env_steps_this_run

        return self.batchs
