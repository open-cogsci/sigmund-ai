from ._base_model import BaseModel


def model(heymans, model, **kwargs):
    """A factory function that returns a Model instance."""
    if model == 'gpt-4':
        from ._openai_model import OpenAIModel
        return OpenAIModel(heymans, 'gpt-4-1106-preview', **kwargs)
    if model == 'gpt-3.5':
        from ._openai_model import OpenAIModel
        return OpenAIModel(heymans, 'gpt-3.5-turbo-1106', **kwargs)
    if model == 'claude-2.1':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(heymans, 'claude-2.1', **kwargs)
    if model == 'claude-3-opus':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(heymans, 'claude-3-opus-20240229', **kwargs)
    if model == 'claude-3-sonnet':
        from ._anthropic_model import AnthropicModel
        return AnthropicModel(heymans, 'claude-3-sonnet-20240229', **kwargs)
    if model.startswith('mistral-'):
        from ._mistral_model import MistralModel
        if not model.endswith('-latest'):
            model += '-latest'
        return MistralModel(heymans, model, **kwargs)
    if model == 'dummy':
        from ._dummy_model import DummyModel
        return DummyModel(heymans, **kwargs)
    raise ValueError(f'Unknown model: {model}')