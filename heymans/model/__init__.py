from ._base_model import BaseModel
from ._openai_model import OpenAIModel
from ._mistral_model import MistralModel
from ._anthropic_model import AnthropicModel


class DummyModel(BaseModel):
    def predict(self, messages):
        return 'dummy reply'
            
        
def model(heymans, model, **kwargs):
    
    if model == 'gpt-4':
        return OpenAIModel(heymans, 'gpt-4-1106-preview', **kwargs)
    if model == 'gpt-3.5':
        return OpenAIModel(heymans, 'gpt-3.5-turbo-1106', **kwargs)
    if model == 'claude-2.1':
        return AnthropicModel(heymans, 'claude-2.1', **kwargs)
    if model == 'claude-3-opus':
        return AnthropicModel(heymans, 'claude-3-opus-20240229', **kwargs)
    if model == 'claude-3-sonnet':
        return AnthropicModel(heymans, 'claude-3-sonnet-20240229', **kwargs)
    if model.startswith('mistral-'):
        if not model.endswith('-latest'):
            model += '-latest'
        return MistralModel(heymans, model, **kwargs)
    if model == 'dummy':
        return DummyModel(heymans, **kwargs)
    raise ValueError(f'Unknown model: {model}')
