# Tensor Agent
Welcome to Civrealm Tensor Agent! This documentation will guide you through the process of training tensor-based agents, specifically using the Proximal Policy Optimization (PPO), in the Civrealm Environment. We will first provide an overview of the Civrealm Tensor Env, followed by instructions on how to use the Civtensor repository to train a PPO agent on this environment.

## 🌏 Civrealm Tensor Environment
The Civrealm Tensor Environment is a reinforcement learning environment wrapped upon Civrealm Base Env specifically designed for training agents using tensor-based algorithms. This environment 

- provides flattened, tensorized observation and action spaces,
- restrict available actions in order to reduce meaningless actions,
- offers delta game score as a basic reward for RL agents,
- provide parallel environments with batched inputs and outputs for efficient training, 

and various modular wrappers which are open to customize your own environment.

## 🏃Using Civtensor Repository



The civtensor repository is a collection of code and utilities that provide a baseline implementation for training reinforcement learning agents using tensor-based algorithms.

It includes an implementation of the PPO algorithm, which we will use to train our agents in the Civrealm Tensor Environment.

### 🏌️ Getting Started
To get started, follow these steps:

1. Clone the tensor-baseline repository from GitHub and enter the directory:
   ```bash
   cd civtensor
   ```
2. Install the required dependencies by navigating to the repository directory and running:
   ```bash
   pip install -e .
   ```
3. Train PPO baseline for fullgame
    ```bash
    cd examples
    python train.py
    ```
4. Train PPO baseline for minitasks:
    ```bash
    cd examples
    python run.py
    ```
   This will start the training process, the agent interacts with the environment, collects experiences, and updates its policy using the PPO algorithm.


5. Monitor the training progress and evaluate the agent's performance using the provided metrics and visualization tools in the tensor-baseline repository.
    ```bash
    cd examples/results/freeciv_tensor_env/$game_type/ppo/installtest/seed-XXXXXXXXX
    # where $game_type = fullgame or minitask
    tensorboard logs/
    ```
Congratulations! You have successfully set up the Civrealm Tensor Agent and trained a PPO agent on the Civrealm Tensor Environment using the tensor-baseline repository.

## Conclusion
In this guide, we introduced the Civrealm Tensor Environment and explained how to use the tensor-baseline repository to train a PPO agent on this environment. We encourage you to explore the various features and customization options available in the Civrealm Tensor Agent and experiment with different reinforcement learning algorithms to further enhance your agent's performance. Happy training!


