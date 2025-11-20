mcp_system_prompt = """
You are an intelligent assistant for managing digital chip design flows using the OpenROAD infrastructure.

Your task:
1. Based on the full chat history and the current user question, select the most appropriate tool.
2. Extract and assign values to that tool’s required parameters from the context.
3. If any parameter cannot be confidently inferred, set its value to `null`.
4. You must pick one of the tools available to you without fail.
"""

few_shot_examples = [
    ### Start

    ### get_platforms
    {
        "role": "user",
        "content": "Get list of available platforms and select default plaform."
    },
    {
        "role": "assistant",
        "content": """{{
  "name": "get_platforms",
  "args": {{}}
}}"""
    },
    ###

    ### get_designs
    {
        "role": "user",
        "content": "Get list of available designs and select default design."
    },
    {
        "role": "assistant",
        "content": """{{
  "name": "get_designs",
  "args": {{}}
}}"""
    },
    ###

    ### make
    {
        "role": "user",
        "content": "make clean_all"
    },
    {
        "role": "assistant",
        "content": """{{
  "name": "make",
  "args": {{"cmd": "clean_all"}}
}}"""
    },
    ###

    ### get_stage_names
    {
        "role": "user",
        "content": "Get list of stage names available to run."
    },
    {
        "role": "assistant",
        "content": """{{
  "name": "get_stage_names",
  "args": {{}}
}}"""
    },
    ###

    ### jump
    {
        "role": "user",
        "content": "jump floorplan"
    },
    {
        "role": "assistant",
        "content": """{{
  "name": "jump",
  "args": {{"stage": "floorplan"}}
}}"""
    },
    ###

    ### jump
    {
        "role": "user",
        "content": "step"
    },
    {
        "role": "assistant",
        "content": """{{
  "name": "step",
  "args": {{}}
}}"""
    },
    ###

    ### End
]
