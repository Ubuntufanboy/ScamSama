from neuro_api.command import Action
from neuro_api.api import NeuroAction
from typing import List, Dict

def mute_bot(actionData: NeuroAction) -> None:
    pass

def unmute_bot(actionData: NeuroAction) -> None:
    pass

action_list: List[Action] = [
    {
        "name": "mute",
        "description": "Mutes the Discord bot."
    },
    {
        "name": "unmute",
        "description": "Unmutes the discord bot"
    }
]
action_functions: Dict[str, function] = {
    "mute": mute_bot,
    "unmute": unmute_bot,
}