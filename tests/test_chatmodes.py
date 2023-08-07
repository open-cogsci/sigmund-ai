from pathlib import Path
# import sys
# sys.path.append(str(Path(__file__).parent.parent))
from heymans import chatmodes, config
import argparse
from datetime import datetime
import re
import logging
logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)


VALIDATION_MODEL = 'gpt-4'
VALIDATION_TEMPLATE = '''I would like you to check the answer provided below. Briefly motivate why the answer does or does not meet the requirements. End your reply with "score:", were score is a value between 0 (really poor) and 5 (excellent), with 3 or higher being an acceptable answer.

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
    testlog = Path(testlog_folder) / f'testlog.{str(datetime.now())}.{config.model}.log'


def read_testcases():
    md_content = Path('tests/testcases.md').read_text()
    test_case_pattern = re.compile(r'# (.*)\n')
    test_cases = test_case_pattern.split(md_content)[1:]
    output = {}
    for i in range(0, len(test_cases), 2):
        title = test_cases[i]
        body = test_cases[i+1]
        question, requirements = re.split(r'The answer should:', body)
        output[title] = {
            'question': question.strip(),
            'requirements': 'The answer should:' + requirements.strip(),
        }
    return output


def score_testcase(description, question, requirements):
    chat_history = {'messages': [{"role": "user", "content": question}]}
    answer, _ = chatmodes.qa(chat_history)
    test_model = config.model
    config.model = VALIDATION_MODEL
    validation_response = chatmodes.predict(
        VALIDATION_TEMPLATE.format(requirements=requirements, answer=answer))
    config.model = test_model
    logger.debug('Question:')
    logger.debug(question)
    logger.debug('Answer:')
    logger.debug(answer)
    logger.debug('Validation response:')
    logger.debug(validation_response)
    score = float(validation_response.lower().split('score:')[-1].strip(' .'))
    with testlog.open('a') as fd:
        fd.write(f'# {description}\n\nQuestion:\n{question}\n\nAnswer:\n\n{answer}\n\nValidation response:\n{validation_response}\n\n')
    return score


def score_testcases(select_cases=None):
    results = []
    for description, testcase in read_testcases().items():
        if select_cases is not None and description not in select_cases:
            results.append((None, description))
            continue
        score = score_testcase(description, **testcase)
        results.append((score, description))
    for score, description in results:
        if score is None:
            print(f'SKIP: testing {description}')
        elif score < 3:
            print(f'FAIL: testing {description}, score: {score}')
        else:
            print(f'PASS: testing {description}, score: {score}')
            
            
def test_gpt4():
    config.model = 'gpt-4'
    init_testlog()
    score_testcases()
    

def test_gpt35turbo():
    config.model = 'gpt-3.5-turbo'
    init_testlog()
    score_testcases()
