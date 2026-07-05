from ._base_model import BaseModel
from .. import config

MISTRAL_MODELS = {
    'mistral-small-latest': 'mistral-small-latest',
    'mistral-medium-3-5': 'mistral-medium-3-5',
    'mistral-medium-3-5-thinking': 'mistral-medium-3-5',
}

OPENAI_MODELS = {
    'gpt-5.5-thinking': 'gpt-5.5',
    'gpt-5.5': 'gpt-5.5',
    'gpt-5.4-thinking': 'gpt-5.4',
    'gpt-5.4': 'gpt-5.4',
    'gpt-5.4-mini': 'gpt-5.4-mini',
    'gpt-5.4-nano': 'gpt-5.4-nano'
}
ANTHROPIC_MODELS = {
    'claude-4-5-haiku': 'claude-haiku-4-5',
    'claude-4-6-sonnet': 'claude-sonnet-4-6',
    'claude-4-6-sonnet-thinking': 'claude-sonnet-4-6',
    'claude-4-7-opus': 'claude-opus-4-7',
    'claude-4-7-opus-thinking': 'claude-opus-4-7',
    'claude-4-8-opus': 'claude-opus-4-8',
    'claude-4-8-opus-thinking': 'claude-opus-4-8',
    'claude-5-fable': 'claude-fable-5'
}
Z_MODELS = {
     'GLM-4.5-Air': 'GLM-4.5-Air',
     'GLM-5.2': 'GLM-5.2',
     'GLM-5.2-thinking': 'GLM-5.2',
     'GLM-5V-Turbo': 'GLM-5V-Turbo'
}


def model(sigmund, model, **kwargs):
    """A factory function that returns a Model instance."""
    if model.endswith('-thinking'):
        kwargs['thinking'] = True
    if model == 'dummy' or config.dummy_model:
        from ._dummy_model import DummyModel
        return DummyModel(sigmund, 'dummy', **kwargs)
    if model in OPENAI_MODELS:
        from ._openai_model import OpenAIModel
        return OpenAIModel(sigmund, OPENAI_MODELS[model], **kwargs)
    if model in ANTHROPIC_MODELS:
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(sigmund, ANTHROPIC_MODELS[model], **kwargs)
    if 'mistral' in model or 'ministral' in model or 'magistral' in model:
        from ._mistral_model import MistralModel
        return MistralModel(sigmund, MISTRAL_MODELS[model], **kwargs)
    if model in Z_MODELS:
        from ._z_model import ZModel
        return ZModel(sigmund, Z_MODELS[model], **kwargs)
    raise ValueError(f'Unknown model: {model}')
