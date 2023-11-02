from civrealm.freeciv.utils.freeciv_logging import fc_logger

from .core import Wrapper, wrapper_override


@wrapper_override(["info"])
class GameOverScoreInfo(Wrapper):
    def info(self, info, terminated=False, truncated=False):
        last_scores = {}
        if terminated or truncated:
            game_scores = self.unwrapped.evaluate_game()[-1]
            last_scores = {k: v[0][-1] for k, v in game_scores.items()}
        info["scores"] = last_scores
        return info


@wrapper_override(["info"])
class MiniTaskGameOverScoreInfo(Wrapper):
    def info(self, info):
        # TODO: Add other metrics
        last_scores = {}
        last_scores["score"] = self.unwrapped.overall_mini_score
        info["scores"] = last_scores
        info["scores"]["success"] = info["minitask"]["success"]
        return info
