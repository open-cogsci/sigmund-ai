from ._base_model import BaseModel


def model(sigmund, model, **kwargs):
    """A factory function that returns a Model instance."""
    if model in ('gpt-4', 'gpt-4o'):
        from ._openai_model import OpenAIModel
        return OpenAIModel(sigmund, 'gpt-4o', **kwargs)
    if model == 'gpt-4o-mini':
        from ._openai_model import OpenAIModel
        return OpenAIModel(sigmund, 'gpt-4o-mini', **kwargs)
    if model == 'gpt-3.5':
        from ._openai_model import OpenAIModel
        return OpenAIModel(sigmund, 'gpt-3.5-turbo', **kwargs)
    if model == 'claude-2.1':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(sigmund, 'claude-2.1', **kwargs)
    if model == 'claude-3-opus':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(sigmund, 'claude-3-opus-20240229', **kwargs)
    if model == 'claude-3-sonnet':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(sigmund, 'claude-3-sonnet-20240229', **kwargs)
    if model == 'claude-3.5-sonnet':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(sigmund, 'claude-3-5-sonnet-latest', **kwargs)
    if model == 'claude-3-haiku':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(sigmund, 'claude-3-haiku-20240307', **kwargs)
    if model == 'claude-3.5-haiku':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(sigmund, 'claude-3-5-haiku-latest', **kwargs)
    if 'mistral' in model:
        from ._mistral_model import MistralModel
        return MistralModel(sigmund, model, **kwargs)
    if model == 'dummy':
        from ._dummy_model import DummyModel
        return DummyModel(sigmund, **kwargs)
    raise ValueError(f'Unknown model: {model}')
