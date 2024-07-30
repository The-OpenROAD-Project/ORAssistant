import os

from src.api.routers import graphs

if __name__ == '__main__':
    rg = graphs.rg
    os.system('clear')

    while True:
        user_question = input('>>> ')
        inputs = {
            'messages': [
                ('user', user_question),
            ]
        }

        if rg.graph is not None:
            output = list(rg.graph.stream(inputs))
        else:
            raise ValueError('RetrieverGraph not initialized.')

        if (
            isinstance(output, list)
            and len(output) > 2
            and 'generate' in output[2]
            and 'messages' in output[2]['generate']
            and len(output[2]['generate']['messages']) > 0
        ):
            llm_response = output[2]['generate']['messages'][0]
        else:
            print('LLM response extraction failed')

        print(f'\n{llm_response}\n')
