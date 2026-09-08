try:
    from .parallel_tensor_env import ParallelTensorEnv
except ImportError:  # ray is optional (not available on every Python version); the single-env classes work without it
    ParallelTensorEnv = None
from .freeciv_minitask_env import FreecivMinitaskEnv
from .freeciv_base_env import FreecivBaseEnv
from .freeciv_tensor_env import FreecivTensorEnv
from .freeciv_tensor_minitask_env import FreecivTensorMinitaskEnv


from .freeciv_llm_env import FreecivLLMEnv
# Parallel environment
from .freeciv_parallel_env import FreecivParallelEnv
from .freeciv_a3c_env import FreecivA3CEnv
# Minitask environment
