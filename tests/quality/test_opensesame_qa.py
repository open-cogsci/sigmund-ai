from pathlib import Path
import statistics
from sigmund import config
from sigmund.model import model as ModelCls
from sigmund.sigmund import Sigmund
from sigmund.database import models
from sigmund import prompt
from datetime import datetime
import json
import logging
logger = logging.getLogger('sigmund')
logging.basicConfig(level=logging.INFO, force=True)
models.init_db()

prompt.SYSTEM_PROMPT_ANSWER = '''You are Sigmund, a brilliant assistant for users of OpenSesame, a program for building psychology and neuroscience experiments. You sometimes use emojis.

# Current date and time

{{ current_datetime }}'''


VALIDATION_TEMPLATE = '''Check the answer provided below. Briefly motivate why the answer does or does not meet the requirements. Reply in the following JSON format, were score is a value between 0 (really poor) and 5 (excellent), with 3 or higher being an acceptable answer.
    
{{
  "score": 4,
  "motivation": "The answer is mostly correct, but could be more precise, because [...]"
}}

Requirements:
{requirements}

Answer:
{answer}

Reply with only the JSON response. Do not add anything else.
'''
VALIDATION_MODELS = 'gpt-5', 'claude-4-sonnet', 'mistral-medium-latest'


def init_testlog():
    global testlog
    testlog_folder = Path(__file__).parent / 'testlog'
    if not testlog_folder.exists():
        testlog_folder.mkdir()
    testlog = Path(testlog_folder) / f'testlog.{datetime.now().strftime("%Y-%m-%d %H:%M")}.{config.settings_default["model_config"]}.log'


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


def score_testcase(description, question, requirements, n=2):
    config.search_collections = {'opensesame'}
    sigmund = Sigmund(user_id='pytest', tools=[])
    scores = []
    for model in VALIDATION_MODELS:
        validation_model = ModelCls(sigmund, model)
        validation_model.json_mode = True
        for reply in sigmund.send_user_message(question):
            pass
        answer = reply.msg
        for i in range(5):
            try:
                validation_response = validation_model.predict(
                    VALIDATION_TEMPLATE.format(requirements=requirements,
                                               answer=answer))
                validation_response = json.loads(validation_response)
            except json.JSONDecodeError as e:
                logger.warning(validation_response)
                logger.warning(f'failed to parse validation answer: {e}')
                continue
            if 'score' not in validation_response:
                logger.warning(validation_response)
                logger.warning('missing score field')
                continue
            score = validation_response['score']
            break
        else:
            raise Exception('Failed to parse any validation responses')
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
            

def test_openai():
    config.settings_default['model_config'] = 'openai'
    init_testlog()
    score_testcases()


def test_openai_thinking():
    config.settings_default['model_config'] = 'openai_thinking'
    init_testlog()
    score_testcases()
    

def test_mistral():
    config.settings_default['model_config'] = 'mistral'
    init_testlog()
    score_testcases()


def test_anthropic_regular():
    config.settings_default['model_config'] = 'anthropic'
    init_testlog()
    score_testcases()
    
    
def test_anthropic_thinking():
    config.settings_default['model_config'] = 'anthropic_thinking'
    init_testlog()
    score_testcases()


config.max_tokens_per_hour = float('inf')
