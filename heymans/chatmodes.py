import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts.prompt import PromptTemplate
from . import config, library


def practice(chat_history):
    if config.model == 'dummy':
        return dummy(chat_history)
    response = openai.ChatCompletion.create(
        model=config.model, messages=chat_history['messages'])
    answer = config.response_rewriter(response.choices[0].message['content'])
    return answer, None


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
    qa = ConversationalRetrievalChain.from_llm(
        llm, library.load_library(), return_generated_question=True,
        return_source_documents=True,
        max_tokens_limit=config.max_source_tokens)
    question = chat_history['messages'][-1]['content']
    result = qa({'question': question, 'chat_history': qa_history})
    sources = [source.metadata for source in result['source_documents']]
    answer = config.response_rewriter(result['answer'])
    return answer, sources


def predict(msg):
    if config.model == 'dummy':
        return 'Dummy prediction'
    llm = ChatOpenAI(model=config.model, openai_api_key=config.openai_api_key)
    return llm.predict(msg)


def dummy(chat_history):
    if len(chat_history['messages']) > 3:
        ai_message = 'Finished <FINISHED>'
    else:
        ai_message = 'Dummy response'
    sources = [{'url': 'https://sigmundai.eu', 'title': 'Sigmund AI'}]
    return ai_message, sources
