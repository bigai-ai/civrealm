from .core import wrapper_override
from .info_wrapper import Wrapper


@wrapper_override(["info", "action"])
class CombineTechResearchGoal(Wrapper):
    def __init__(self, env):
        self.tech_actions = {}
        super().__init__(env)

    def info(self, info, observation):
        self.tech_actions = {}
        info_tech = info["available_actions"].get("tech", {"cur_player": {}})[
            "cur_player"
        ]
        if len(info_tech) == 0:
            return info
        for tech_id, tech in observation["tech"].items():
            tech_arg = f"{tech['name']}_{tech_id}"
            goal = info_tech.pop(f"set_tech_goal_{tech_arg}", False)
            tech_aciton = "research " + tech_arg
            info_tech[tech_aciton] = (
                info_tech.pop(f"research_tech_{tech_arg}", False) or goal
            )
            if goal:
                self.tech_actions["research " + tech_arg] = f"set_tech_goal_{tech_arg}"
            else:
                self.tech_actions["research " + tech_arg] = f"research_tech_{tech_arg}"
        info["available_actions"]["tech"][
            self.get_wrapper_attr("my_player_id")
        ] = info_tech
        info["available_actions"]["tech"].pop("cur_player")
        return info

    def action(self, action):
        if action is None:
            return action
        if action[0] != "tech":
            return action
        return (action[0], "cur_player", self.tech_actions[action[2]])
