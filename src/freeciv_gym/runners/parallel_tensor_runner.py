import gymnasium
import freeciv_gym
from freeciv_gym.freeciv.utils.freeciv_logging import ray_logger_setup
from freeciv_gym.envs.parallel_tensor_env import ParallelTensorEnv
from freeciv_gym.configs import fc_args
import ray
import copy
from civtensor.models.agent import Agent

class ParallelTensorRunner:
    def __init__(self, env_name, agent, logger, epoch_num):
        ray.init(local_mode=False, runtime_env={"worker_process_setup_hook": ray_logger_setup})
        self.logger = ray_logger_setup()

        self.tensor_env = ParallelTensorEnv('freeciv/FreecivTensor-v0', None, 3)
        self.agent = Agent()
        self.steps = 0
        self.batch_size_run = fc_args['batch_size_run']
        # self.t = 0
        # self.t_env = 0

        # self.batchs = []
        # self.train_returns = []
        # self.test_returns = []
        # self.train_stats = {}
        # self.test_stats = {}

        # self.log_train_stats_t = -100000

    def close(self):
        ray.shutdown()

    def reset(self):
        return self.tensor_env.reset()

    def run(self, test_mode=False):
        observations, infos = self.reset()
        while self.steps < fc_args['trainer.max_steps']:
            actions = self.agent(observations, infos)
            observations, rewards, terminated, truncated, infos = self.tensor_env(actions)
    
            self.steps += self.batch_size_run
