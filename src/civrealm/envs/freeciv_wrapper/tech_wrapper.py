from .info_wrapper import Wrapper


class AlwaysSetResearchGoal(Wrapper):
    def __init__(self, env):
        self.tech_goals = {}
        super().__init__(env)

    def reset(self, *, seed=None, options=None, **kwargs):
        obs, info = self.env.reset(seed=seed, options=options, **kwargs)
        return obs, self.info(info, obs)

    def step(self, action):
        action = self.action(action)
        obs, reward, terminated, truncated, info = self.env.step(action)
        info = self.info(info, obs)
        return obs, reward, terminated, truncated, info

    def info(self, info, obs):
        self.tech_goals = {}
        for tech_id, tech in obs["tech"]:
            tech_arg = f"{tech['name']}_{tech_id}"
            goal = info["available_actions"]["tech"]["cur_player"].pop(
                f"set_tech_goal_{tech_arg}"
            )
            info["available_actions"]["tech"]["cur_player"][tech_arg] = goal or info[
                "available_actions"
            ]["tech"]["cur_player"].pop(f"tech_research_{tech_arg}")
            if goal:
                self.tech_goals[tech_arg] = f"set_tech_goal_{tech_arg}"
            else:
                self.tech_goals[tech_arg] = f"tech_research_{tech_arg}"
        return info

    def action(self, action):
        if action[0] != "tech":
            return action
        return (action[0], action[1], self.tech_goals[action[2]])
