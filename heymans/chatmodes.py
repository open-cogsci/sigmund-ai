import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from pathlib import Path
from . import config


def practice(chat_history):
    response = openai.ChatCompletion.create(
        model=config.model, messages=chat_history['messages'])
    return response.choices[0].message['content']
    
    
def qa(chat_history=None):
    if chat_history is None:
        return config.qa_start_message
    questions = chat_history['messages'][:-1:2]
    answers = chat_history['messages'][1::2]
    qa_history = [(q['content'], a['content'])
                  for q, a in zip(questions, answers)]
    embeddings_model = OpenAIEmbeddings(openai_api_key=config.openai_api_key)
    data = [TextLoader(src).load()[0]
            for src in Path('sources').glob('**/**/*.txt')]
    db = FAISS.from_documents(data, embeddings_model)
    llm = ChatOpenAI(model='gpt-4', openai_api_key=config.openai_api_key)
    qa = ConversationalRetrievalChain.from_llm(llm, db.as_retriever())
    question = chat_history['messages'][-1]['content']
    result = qa({'question': question, 'chat_history': qa_history})
    return result['answer']
