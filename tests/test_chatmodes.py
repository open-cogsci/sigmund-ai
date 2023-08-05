from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from heymans import chatmodes, config
import argparse
import logging
logger = logging.getLogger('heymans')
import re


TEST_MODEL = 'gpt-4'
# TEST_MODEL = 'gpt-3.5-turbo'
VALIDATION_MODEL = 'gpt-4'
VALIDATION_TEMPLATE = '''I would like you to check the answer provided below. Briefly motivate why the answer does or does not meet the requirements. End your reply with "score:", were score is a value between 0 (really poor) and 5 (excellent), with 3 or higher being an acceptable answer.

Requirements:
{requirements}

Answer:
{answer}
'''


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


def score_testcase(question, requirements):
    chat_history = {'messages': [{"role": "user", "content": question}]}
    config.model = TEST_MODEL
    answer, _ = chatmodes.qa(chat_history)
    config.model = VALIDATION_MODEL
    validation_response = chatmodes.predict(
        VALIDATION_TEMPLATE.format(requirements=requirements, answer=answer))
    logger.debug('Question:')
    logger.debug(question)
    logger.debug('Answer:')
    logger.debug(answer)
    logger.debug('Validation response:')
    logger.debug(validation_response)
    score = float(validation_response.lower().split('score:')[-1].strip(' .'))
    testlog = Path('tests/testcases.log')
    # testlog.touch()
    with testlog.open('a') as fd:
        fd.write(f'---\nTest model:\n{TEST_MODEL}\n\nQuestion:\n{question}\n\nAnswer:\n\n{answer}\n\nValidation response:\n{validation_response}\n\n')
    return score


def test_qa(select_cases=None):
    results = []
    for description, testcase in read_testcases().items():
        if select_cases is not None and description not in select_cases:
            results.append((None, description))
            continue
        score = score_testcase(**testcase)
        results.append((score, description))
    for score, description in results:
        if score is None:
            print(f'SKIP: testing {description}')
        elif score < 3:
            print(f'FAIL: testing {description}, score: {score}')
        else:
            print(f'PASS: testing {description}, score: {score}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', action='store',
                        help='A comma-separated list of test cases to be run')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG, force=True)
    test_qa(args.cases)
