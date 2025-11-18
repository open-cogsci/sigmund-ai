from ._base_model import BaseModel
from .. import config


OPENAI_MODELS = {
    'o1': 'o1',
    'o3': 'o3',
    'o3-mini': 'o3-mini',
    'o4-mini': 'o4-mini',
    'gpt-5.1-thinking': 'gpt-5.1',
    'gpt-5.1': 'gpt-5.1',
    'gpt-5-thinking': 'gpt-5',
    'gpt-5': 'gpt-5',
    'gpt-5-mini': 'gpt-5-mini',
    'gpt-5-nano': 'gpt-5-nano',
    'gpt-4.1': 'gpt-4.1',
    'gpt-4.1-mini': 'gpt-4.1-mini',
    'gpt-4': 'gpt-4o',
    'gpt-4o': 'gpt-4o',
    'gpt-4o-mini': 'gpt-4o-mini',
    'gpt-3.5': 'gpt-3.5-turbo'
}
ANTHROPIC_MODELS = {
    'claude-2.1': 'claude-2.1',
    # Haiku
    'claude-3-haiku': 'claude-3-haiku-20240307',
    'claude-3.5-haiku': 'claude-3-5-haiku-latest',
    'claude-4-5-haiku': 'claude-haiku-4-5',
    # Sonnet
    'claude-3-sonnet': 'claude-3-sonnet-20240229',
    'claude-3.5-sonnet': 'claude-3-5-sonnet-latest',
    'claude-3.7-sonnet': 'claude-3-7-sonnet-latest',
    'claude-3.7-sonnet-thinking': 'claude-3-7-sonnet-latest',
    'claude-4-sonnet': 'claude-sonnet-4-0',
    'claude-4-5-sonnet': 'claude-sonnet-4-5',
    'claude-4-sonnet-thinking': 'claude-sonnet-4-0',
    'claude-4-5-sonnet-thinking': 'claude-sonnet-4-5',
    # Opus
    'claude-3-opus': 'claude-3-opus-20240229',
    'claude-4-opus': 'claude-opus-4-0',
    'claude-4-opus-thinking': 'claude-opus-4-0',
    'claude-4-1-opus': 'claude-opus-4-1',
    'claude-4-1-opus-thinking': 'claude-opus-4-1',
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
        return MistralModel(sigmund, model, **kwargs)
    raise ValueError(f'Unknown model: {model}')
