# Tensor Agent
Welcome to Civrealm Tensor Agent! This documentation will guide you through the process of training tensor-based agents, specifically using the Proximal Policy Optimization (PPO), in the Civrealm Environment. We will first provide an overview of the Civrealm Tensor Env, followed by instructions on how to use the civrealm-tensor-baseline repository to train a PPO agent on this environment.

## 🌏 Civrealm Tensor Environment
The Civrealm Tensor Environment is a reinforcement learning environment wrapped upon Civrealm Base Env specifically designed for training agents using tensor-based algorithms. This environment 

- provides flattened, tensorized observation and action spaces,
- restrict available actions in order to reduce meaningless actions,
- offers delta game score as a basic reward for RL agents,
- provide parallel environments with batched inputs and outputs for efficient training, 

and various modular wrappers which are open to customize your own environment.


## 🤖 Network Architecture for a Tensor Agent

![Tensor Architecture](../assets/tensor-architecture.png)

To effectively handle multi-source and variable-length inputs, we draw inspiration from [AlphaStar](https://www.nature.com/articles/s41586-019-1724-z) and implement a serialized hierarchical feature extraction and action selection approach, as shown above. This method involves generating layered actions and predicting value function outputs, and our neural network architecture comprises three main components: representation learning, action selection, and value estimation.

**Representation**. At the representation level, we adopt a hierarchical structure. In the lower layer, we extract controller features using various models like MLP, Transformer, and CNN, depending on whether the input is a single vector, sequence, or image-based. These extracted features are then fed into a transformer to facilitate attention across different entities, creating globally meaningful representations. Additionally, we utilize an RNN to combine the current-state features with the memory state, enabling conditional policy decisions based on the state history.

**Action selection**. At the action selection level, we leverage the learned representations to make decisions. In the actor selection module, we determine the primary action category to be executed, including options like unit, city, government, technology, diplomacy, or termination. Subsequently, we employ a pointer network to select the specific action ID to be executed, followed by the determination of the exact action to be performed.

**Value estimation**. To enable the use of an actor-critic algorithm, we incorporate a value prediction head after the representation learning phase. This shared representation part of the network benefits both the actor and critic, enhancing training efficiency.

**Training**. We use the [Proximal Policy Optimization (PPO)](https://arxiv.org/abs/1707.06347) algorithm to train the agent. To mitigate the on-policy sample complexity of PPO, we harness [Ray](https://www.ray.io/) for parallelizing tensor environments, optimizing training speed and efficiency.



## 🏃 Using civrealm-tensor-baseline Repository



The civrelam-tensor-baseline repository is a collection of code and utilities that provide a baseline implementation for training reinforcement learning agents using tensor-based algorithms.

It includes an implementation of the PPO algorithm, which we will use to train our agents in the Civrealm Tensor Environment.

### 🏌️ Getting Started
To get started, follow these steps:

1. Clone the civrealm-tensor-baseline repository from GitHub and enter the directory:
   ```bash
   cd civrealm-tensor-baseline
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


5. Monitor the training progress and evaluate the agent's performance using the provided metrics and visualization tools in the civrealm-tensor-baseline repository.
    ```bash
    cd examples/results/freeciv_tensor_env/$game_type/ppo/installtest/seed-XXXXXXXXX
    # where $game_type = fullgame or minitask
    tensorboard logs/
    ```
Congratulations! You have successfully set up the Civrealm Tensor Agent and trained a PPO agent on the Civrealm Tensor Environment using the civrealm-tensor-baseline repository.

## Conclusion
In this guide, we introduced the Civrealm Tensor Environment and explained how to use the civrealm-tensor-baseline repository to train a PPO agent on this environment. We encourage you to explore the various features and customization options available in the Civrealm Tensor Agent and experiment with different reinforcement learning algorithms to further enhance your agent's performance. Happy training!


