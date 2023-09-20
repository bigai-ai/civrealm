import gymnasium
import freeciv_gym
from freeciv_gym.freeciv.utils.freeciv_logging import ray_logger_setup
from freeciv_gym.envs.parallel_tensor_env import ParallelTensorEnv
from freeciv_gym.configs import fc_args
import ray
import copy


class ParallelTensorRunner:
    def __init__(self, env_name, agent, logger, epoch_num):
        ray.init(
            local_mode=False,
            runtime_env={"worker_process_setup_hook": ray_logger_setup},
        )
        self.logger = ray_logger_setup()

        self.tensor_env = ParallelTensorEnv(env_name, 4, 6300)
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
            actions = self.agent(observations, infos)
            observations, rewards, terminated, truncated, infos = self.tensor_env.step(
                actions
            )

            self.steps += self.batch_size_run
            if self.steps > 20:
                print(self.tensor_env.get_recent_scores())
        self.close()
