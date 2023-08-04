import openai
import logging
logger = logging.getLogger('heymans')
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts.chat import ChatPromptTemplate, \
    SystemMessagePromptTemplate, HumanMessagePromptTemplate
from datamatrix.functional import memoize
from . import config, library


def practice(chat_history):
    if config.model == 'dummy':
        return dummy(chat_history)
    response = openai.ChatCompletion.create(
        model=config.model, messages=chat_history['messages'])
    answer = config.response_rewriter(response.choices[0].message['content'])
    return answer, None


def _create_wrapper(fnc):
    def inner(*args, **kwargs):
        messages = kwargs['messages']
        system_message = messages[0]
        user_message = messages[0]
        logger.info('Generating Q&A answer (this may occur several times due to retries within the openai libary) ...')
        logger.info(f'Sending {len(messages)} messages')
        for msg in messages:
            logger.info(f'role: {msg["role"]}, length: {len(msg["content"])}, words: {len(msg["content"].split())}')
        # logger.info(f'prompt: {messages[0]}')
        logger.info(f'query: {messages[-1]}')
        result = fnc(*args, **kwargs)
        logger.info('Done generating …')
        return result
    return inner


def qa(chat_history=None):
    if chat_history is None:
        return config.qa_start_message, None
    if config.model == 'dummy':
        return dummy(chat_history)
    questions = chat_history['messages'][:-1:2]
    answers = chat_history['messages'][1::2]
    qa_history = [(q['content'], a['content'])
                  for q, a in zip(questions, answers)]
    llm = ChatOpenAI(model=config.model, openai_api_key=config.openai_api_key)
    llm.client.create = _create_wrapper(llm.client.create)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(config.qa_prompt),
        HumanMessagePromptTemplate.from_template("{question}"),
    ])
    qa = ConversationalRetrievalChain.from_llm(
        llm, library.load_library(), return_generated_question=True,
        return_source_documents=True,
        max_tokens_limit=config.max_source_tokens,
        combine_docs_chain_kwargs={'prompt': prompt})
    question = chat_history['messages'][-1]['content']
    result = qa({'question': question, 'chat_history': qa_history})
    sources = [source.metadata for source in result['source_documents']]
    answer = config.response_rewriter(result['answer'])
    return answer, sources


def predict(msg):
    if config.model == 'dummy':
        return 'Dummy prediction'
    if config.model == 'gpt-4':
        @memoize(persistent=True)
        def inner(msg):
            llm = ChatOpenAI(model=config.model, openai_api_key=config.openai_api_key)
            print('Generating prediction ...')
            print(f'length: {len(msg)}, words: {len(msg.split())}')
            return llm.predict(msg)
        return inner(msg)
    return llm.predict(msg)


def dummy(chat_history):
    if len(chat_history['messages']) > 3:
        ai_message = 'Finished <FINISHED>'
    else:
        ai_message = 'Dummy response'
    sources = [{'url': 'https://sigmundai.eu', 'title': 'Sigmund AI'}]
    return ai_message, sources
