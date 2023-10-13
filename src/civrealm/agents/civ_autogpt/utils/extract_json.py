import json

def extract_json(text):
    # find json
    start_index = text.find("{")
    end_index = text.rfind("}") + 1
    json_string = text[start_index:end_index]
    
    # extract json to dict
    try:
        json_data = json.loads(json_string)
    except json.JSONDecodeError:
        return text
    
    # nested process inner json
    for key, value in json_data.items():
        if isinstance(value, str):
            # if str, extract to json
            nested_json = extract_json(value)
            if nested_json is not None:
                json_data[key] = nested_json
    
    return str(json_data)

# text_with_nested_json = '{"thoughts": {"thought": "I need to generate a guiding action for the user based on the current game state.","reasoning": "The user has provided the current game information, and I have analyzed the situation. I should provide a guiding action for the user to advance the game.","plan": "- identify the command to provide the user with the result\\n- execute the command with the appropriate input\\n- generate the output and return it to the user"},"command": {"name": "finalDecision", "input": {"action": "build"}}}This is my response as an AI assistant. I have analyzed the current game state and determined that the best course of action for the user is to build a settlement. Please let me know if this decision is correct or if you would like me to adjust it based on additional information.'
# nested_json_data = extract_nested_json(text_with_nested_json)
