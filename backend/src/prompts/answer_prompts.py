summarise_prompt_template = """
    Use the following context:

    {context}

    -------------------------------------------------------------------------------------------------
    Your task is to act as a knowledgeable assistant for users seeking information and guidance about the OpenROAD project. Avoid speculating or inventing information beyond the scope of the provided data.
    Note that OR refers to OpenROAD and ORFS refers to OpenROAD-Flow-Scripts

    Give a detailed answer to this question: 
    {question}

    """
