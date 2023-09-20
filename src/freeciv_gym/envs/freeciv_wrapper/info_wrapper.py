from gymnasium.core import Wrapper


class InfoWrapper(Wrapper):
    def __init__(self, env):
        Wrapper.__init__(self, env)

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        return obs, self.info(
            observation=obs,
            info=info,
            terminated=None,
            truncated=None,
            reward=None,
            action=None,
        )

    def step(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        return (
            observation,
            reward,
            terminated,
            truncated,
            self.info(
                observation=observation,
                reward=reward,
                terminated=terminated,
                truncated=truncated,
                info=info,
                action=action,
            ),
        )

    def info(
        self,
        observation=None,
        reward=None,
        terminated=None,
        truncated=None,
        info=None,
        action=None,
    ):
        raise NotImplementedError


class GameOverScoreInfo(InfoWrapper):
    def __init__(self, env):
        InfoWrapper.__init__(self, env)

    def info(self, info, terminated, truncated, **kwargs):
        last_scores = {}
        if terminated or truncated:
            game_scores = self.evaluate_game()[-1]
            last_scores = {k: v[0][-1] for k, v in game_scores.items()}
        info["scores"] = last_scores
        return info

class MiniTaskGameOverScoreInfo(GameOverScoreInfo):
    def __init__(self, env):
        GameOverScoreInfo.__init__(self, env)

    def info(self, info, terminated, truncated, **kwargs):
        info = super().info(info, terminated, truncated, **kwargs)
        info['scores']['score'] = info["minitask"]["mini_score"]
        return info
