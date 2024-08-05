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
            and 'generate' in output[-1]
            and 'messages' in output[-1]['generate']
            and len(output[-1]['generate']['messages']) > 0
        ):
            llm_response = output[-1]['generate']['messages'][0]
        else:
            print('LLM response extraction failed')

        if(
            'tool' in output[-2]
            and 'sources' in output[-2]['tool']
            and 'urls' in output[-2]['tool']
        ):
            tool = list(output[-2].keys())[0]
            srcs = output[-2][tool]['sources']
            urls = output[-2][tool]['urls']
        else:
            print('Tool response extraction failed')

        print(f'LLM: {llm_response} \nSources: {srcs} \nURLs: {urls}\n\n')
