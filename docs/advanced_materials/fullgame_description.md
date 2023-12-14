# Full-Game Characteristics

In the full-game, each player acts as a civilization leader. The objective of players is to guide their civilization from its humble beginnings to the greatest civilization. Civilizations evolve through eras from the Bronze Age to the Space Age and the number of controllable objects (units, cities, diplomatic relations, etc.) explodes as the game progresses. In addition, each decision made typically carries a multi-faceted impact, encompassing both long-term strategic consequences and short-term tactical outcomes. It is worth noting that a favorable tactical outcome may not necessarily translate into a positive strategic outcome. For instance, the immediate construction of a city at the beginning of the game can yield greater resources in the early stages (a tactical advantage). In contrast, settling in a resource-rich area after thorough exploration may result in substantial resource accumulation over the long haul (a strategic advantage). 

Besides the long decision-making horizon, multi-faceted decision impacts, and huge state-action spaces, the full-game exhibits additional characteristics that elevate its complexity: 

**Imperfect info.** Players typically only gain the information discovered by their own units and cities, resulting in partially observable states. Players may also obtain others’ vision by diplomatic actions.

**Stochastic.** The dynamics of the environment is stochastic. Moreover, there exist random events and crises that can disrupt plans, forcing players to adapt on the fly and make tough decisions. 

**Multi-goal.** There are multiple victory paths, i.e., (1) military: conquering all other civilizations; (2) science: being the first civilization that launches a spacecraft destined for Alpha Centauri; and (3) time: obtaining the highest score, computed based on criteria such as civilization size, wealth, cultural accomplishments, and scientific advancements, before reaching a predetermined number of turns, in case the first two conditions are not met. These paths necessitate a delicate balance between economic expansion, military development, diplomatic influence, cultural achievements, and technological research, which poses a high requirement for learning and reasoning. 

**Dynamic space.** As the game unfolds, players continuously produce new units, construct additional cities, engage in battles, and conquer other players. Consequently, the state and action space of a player undergo dynamic changes throughout the gameplay. Designing an effective decision model for the agent to adapt to this evolving space presents a significant challenge. 

**Multi-agent.** Multiple players can interact with one another, including hand-crafted AI players provided by Freeciv on the server side. CivRealm allows multiple agents to connect to the same game simultaneously, facilitating self-play training. 

**General-sum.** Players are free to form alliances or wage war against others, rendering the full game a general-sum game that necessitates considerations of both cooperative and competitive strategies. 

**Changing players.** The number of players can fluctuate during a game due to factors like revolts or civilization conquests, introducing new players controlled by built-in AI or removing existing ones. Such changes often result in significant alterations to the state-action space. 

**Communication.** Players can communicate explicitly using two types of communication: diplomatic actions (e.g., adding a clause) and natural language chat through a chat box. This feature enriches player interactions and enables LLM agents to fully leverage their natural language processing capabilities.

To implement an agent that plays the full-game, it is important to understand the content of the observations returned by the environment and the format of the actions required by the environment. Please check [Observations](fullgame_observation.md) and [Actions](fullgame_action.md) for more details.


