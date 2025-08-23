from neuro_api.api import AbstractNeuroAPI, NeuroAction
from jsonschema import validate, ValidationError, SchemaError
from .actions import action_list

class NeuroAPIProps(AbstractNeuroAPI):
    async def __init__(self, game_title = "Scam-sama", connection = None):
        super().__init__(game_title, connection)
        self._connection = connection
        # Register actions as dicts for external use (name, description, schema)
        self.actions = [action.get_action() for action in action_list]
        await self.send_context("Welcome to your scambaiting session!")

    @property
    def connection(self):
        return self._connection

    async def handle_action(self, actionData: NeuroAction) -> None:
        # Find the action instance by name
        action = next((a for a in action_list if a.name == actionData.name), None)

        if action is None:
            self.send_action_result(actionData.id_, False, "Unknown action.")
            return

        try:
            # Validate against schema if it exists
            if action.schema:
                validate(actionData.data, action.schema)

            # Action results should be sent to validate inputs
            self.send_action_result(actionData.id_, True)
            message = await action.perform_action(actionData)
            self.send_context(message)

        except ValidationError as e:
            self.send_action_result(actionData.id_, False, f"You inputted something invalid: {e}")
        except SchemaError as e:
            self.send_action_result(actionData.id_, True, f"The schema validation broke with this error: {e}\nWe'll try and force the action to go through anyways.")
            try:
                success, message = await action.perform_action(actionData)
                self.send_action_result(actionData.id_, success, message)
            except Exception as e:
                self.send_action_result(actionData.id_, True, f"An error occured: {e}\nGuess that happens when you try and force a command through, eh?")
        except Exception as e:
            print(f"An exception occured: {e}") # TODO: implement logging across both API and bot modes
            self.send_action_result(actionData.id_, True, "An exception occured while running the action.")

    # For actions, refer to actions.py