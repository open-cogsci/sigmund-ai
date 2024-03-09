from pathlib import Path
import unittest
import os
import statistics
from heymans import config
from heymans.heymans import Heymans
from heymans.model import OpenAIModel, DummyModel
from heymans.database import models
from heymans import prompt

import argparse
from datetime import datetime
import re
import logging
logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)
models.init_db()

prompt.SYSTEM_PROMPT_ANSWER = '''You are Sigmund, a brilliant assistant for users of OpenSesame, a program for building psychology and neuroscience experiments. You sometimes use emojis.

# Current date and time

{{ current_datetime }}'''


VALIDATION_TEMPLATE = '''Check the answer provided below. Briefly motivate why the answer does or does not meet the requirements. End your reply with "score:", were score is a value between 0 (really poor) and 5 (excellent), with 3 or higher being an acceptable answer.

Requirements:
{requirements}

Answer:
{answer}
'''


def init_testlog():
    global testlog
    testlog_folder = Path(__file__).parent / 'testlog'
    if not testlog_folder.exists():
        testlog_folder.mkdir()
    testlog = Path(testlog_folder) / f'testlog.{str(datetime.now())}.{config.answer_model}.log'


def read_testcases():
    output = {}
    for path in (Path(__file__).parent / 'testcases').glob('*.md'):
        test_case = path.read_text()
        question, requirements = test_case.split('\n', 1)
        output[path.name] = {
            'question': question.strip(),
            'requirements': requirements.strip()
        }
    logger.info(f'read {len(output)} testcases')
    return output


def score_testcase(description, question, requirements, n=3):
    heymans = Heymans(user_id='pytest')
    validation_model = OpenAIModel(heymans, 'gpt-4-1106-preview')
    scores = []
    for i in range(n):
        for answer, documentation in heymans.send_user_message(question):
            pass
        while True:
            validation_response = validation_model.predict(
                VALIDATION_TEMPLATE.format(requirements=requirements, answer=answer))
            logger.info('Question:')
            logger.info(question)
            logger.info('Answer:')
            logger.info(answer)
            logger.info('Validation response:')
            logger.info(validation_response)
            try:
                score = float(validation_response.lower().split('score:')[-1].strip(' .')[0])
            except Exception as e:
                logger.warning(f'failed to parse validation answer: {e}')
            else:
                break
        scores.append(score)
        with testlog.open('a') as fd:
            fd.write(f'*********\n\n# {description}\n\nQuestion:\n{question}\n\nAnswer:\n\n{answer}\n\nValidation response:\n\n{validation_response}\n\n')
    return scores


def score_testcases(select_cases=None):
    results = []
    for description, testcase in read_testcases().items():
        if select_cases is not None and description not in select_cases:
            results.append((None, description))
            continue
        scores = score_testcase(description, **testcase)
        results.append((scores, description))
    with testlog.open('a') as fd:
        fd.write('\n\nSummary:\n')
        for scores, description in results:
            if scores is None:
                score = None
            else:
                score = statistics.mean(scores)
            if score is None:
                s = f'SKIP: testing {description}'
            elif score < 3:
                s = f'FAIL: testing {description}, score: {score} ({scores})'
            else:
                s = f'PASS: testing {description}, score: {score} ({scores})'
            print(s)
            fd.write(s + '\n')
            

def test_gpt4():
    config.search_model = 'gpt-3.5'
    config.condense_model = 'gpt-3.5'
    config.answer_model = 'gpt-4'
    init_testlog()
    score_testcases()
    

def test_gpt4mistral():
    config.search_model = 'mistral-medium'
    config.condense_model = 'mistral-medium'
    config.answer_model = 'gpt-4'
    init_testlog()
    score_testcases()


def test_mistral():
    config.search_model = 'mistral-medium'
    config.condense_model = 'mistral-medium'
    config.answer_model = 'mistral-large'
    init_testlog()
    score_testcases()


def test_claude3opus():
    config.search_model = 'mistral-medium'
    config.condense_model = 'claude-3-sonnet'
    config.answer_model = 'claude-3-opus'
    init_testlog()
    score_testcases()


config.max_tokens_per_hour = float('inf')
