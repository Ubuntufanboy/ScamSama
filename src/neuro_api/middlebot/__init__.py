from neuro_api.api import AbstractNeuroAPI, NeuroAction
from jsonschema import validate, ValidationError, SchemaError
from .actions import action_list, action_functions

class NeuroAPIProps(AbstractNeuroAPI):
    async def __init__(self, game_title = "Scam-sama", connection = None):
        super().__init__(game_title, connection) # Initialises using the startup command
        self._connection = connection # assigns a connection
        self.actions = action_list # Assign list of actions and their schema/functions
        await self.send_context("Welcome to your scambaiting session!") # Initial context to let Neuro know
    
    @property
    def connection(self):
        return self._connection

    async def handle_action(self, actionData: NeuroAction) -> None:
        # Find the action definition in action_list
        action_def = next((action for action in action_list if action["name"] == actionData.name), None)
        
        if action_def is None:
            self.send_action_result(actionData.id_, False, "Unknown action.")
            return
            
        # Check if action function exists
        if actionData.name not in action_functions:
            self.send_action_result(actionData.id_, False, "Action function not implemented.")
            return
            
        try:
            # Validate against schema if it exists
            if "schema" in action_def:
                validate(actionData.data, action_def["schema"])
            
            self.send_action_result(actionData.id_, True)
            
            # Execute the action function
            action_function = action_functions[actionData.name]
            action_function(actionData)
            
        except ValidationError as e:
            self.send_action_result(actionData.id_, False, f"You inputted something invalid: {e}")
        except SchemaError as e:
            self.send_action_result(actionData.id_, True, f"The schema validation broke with this error: {e}\nWe'll try and force the action to go through anyways.")
            try:
                action_function = action_functions[actionData.name]
                action_function(actionData)
            except Exception as e:
                self.send_action_result(actionData.id_, True, f"An error occured: {e}\nGuess that happens when you try and force a command through, eh?")
        except Exception as e:
            print(f"An exception occured: {e}") # TODO: implement logging across both API and bot modes
            self.send_action_result(actionData.id_, True, "An exception occured while running the action.")
    
    # For actions, refer to actions.py