import gymnasium
import civrealm
from civrealm.freeciv.utils.freeciv_logging import ray_logger_setup
from civrealm.envs.parallel_tensor_env import ParallelTensorEnv
from civrealm.envs.parallel_self_play_env import ParallelSelfPlayEnv
from civrealm.configs import fc_args
import ray
import copy


class ParallelTensorRunner:
    def __init__(self, env_name, agent, logger, epoch_num):
        ray.init(
            local_mode=False,
            runtime_env={"worker_process_setup_hook": ray_logger_setup},
        )
        self.logger = ray_logger_setup()

        # self.tensor_env = ParallelTensorEnv(env_name, fc_args["batch_size_run"])
        self.tensor_env = ParallelSelfPlayEnv(env_name, fc_args["batch_size_run"])
        self.agent = agent
        self.steps = 0
        self.batch_size_run = fc_args["batch_size_run"]

    def close(self):
        ray.shutdown()

    def reset(self):
        return self.tensor_env.reset()

    def run(self, test_mode=False):
        observations, infos = self.reset()
        while self.steps < fc_args["trainer.max_steps"]:
            actions = self.agent.act(observations, infos)
            observations, rewards, terminated, truncated, infos = self.tensor_env.step(
                actions
            )
            self.steps += self.batch_size_run
            # print(f'Steps: {self.steps}')
            if self.steps%20 == 0:
                print(f'Recent score: {self.tensor_env.get_recent_scores()}')
        self.close()
