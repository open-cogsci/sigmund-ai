from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from heymans import config
from heymans.heymans import Heymans
from heymans.model import GPT4Model
import argparse
from datetime import datetime
import re
import logging
logger = logging.getLogger('heymans')
logging.basicConfig(level=logging.INFO, force=True)


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
    for path in Path('tests/testcases').glob('*.md'):
        test_case = path.read_text()
        question, requirements = test_case.split('\n', 1)
        output[path.name] = {
            'question': question.strip(),
            'requirements': requirements.strip()
        }
    logger.info(f'read {len(output)} testcases')
    return output


def score_testcase(heymans, validation_model, description, question,
                   requirements):
    chat_history = {'messages': [{"role": "user", "content": question}]}
    answer, documentation = heymans.send_user_message(question)
    validation_response = validation_model.predict(
        VALIDATION_TEMPLATE.format(requirements=requirements, answer=answer))
    logger.info('Question:')
    logger.info(question)
    logger.info('Answer:')
    logger.info(answer)
    logger.info('Validation response:')
    logger.info(validation_response)
    score = float(validation_response.lower().split('score:')[-1].strip(' .')[0])
    with testlog.open('a') as fd:
        fd.write(f'*********\n\n# {description}\n\nQuestion:\n{question}\n\nAnswer:\n\n{answer}\n\nValidation response:\n\n{validation_response}\n\n')
    return score


def score_testcases(select_cases=None):
    heymans = Heymans(user_id='pytest')
    validation_model = GPT4Model(heymans)
    results = []
    for description, testcase in read_testcases().items():
        if select_cases is not None and description not in select_cases:
            results.append((None, description))
            continue
        score = score_testcase(heymans, validation_model, description, **testcase)
        results.append((score, description))
    for score, description in results:
        if score is None:
            print(f'SKIP: testing {description}')
        elif score < 3:
            print(f'FAIL: testing {description}, score: {score}')
        else:
            print(f'PASS: testing {description}, score: {score}')
            
            
def test_gpt4():
    config.answer_model = 'gpt-4'
    init_testlog()
    score_testcases()
    

def test_gpt35():
    config.answer_model = 'gpt-3.5'
    init_testlog()
    score_testcases()
    
    
def test_claude21():
    config.answer_model = 'claude-2.1'
    init_testlog()
    score_testcases()


if __name__ == '__main__':
    import logging; logging.basicConfig(level=logging.INFO, force=True)
    test_gpt4()
    # test_gpt35()
    # test_claude21()
