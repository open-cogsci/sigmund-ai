from . import BaseTool
import logging
import requests
from .. import config
logger = logging.getLogger('sigmund')


class generate_image(BaseTool):
    """Generate an image based on a text description."""
    
    arguments = {
        'prompt': {
            'type': 'string',
            'description': 'The image description',
        },
        'quality': {
            'type': 'string',
            'description': 'The quality of the image. Use standard unless there is a good reason to use HD.',
            'enum': ['standard', 'hd']
        },
        'size': {
            'type': 'string',
            'description': 'The size of the image in pixels',
            'enum': ['1024x1024', '1792x1024', '1024x1792']
        },
        'style': {
            'type': 'string',
            'description': 'Vivid causes the model to lean towards generating hyper-real and dramatic images. Natural causes the model to produce more natural, less hyper-real looking images.',
            'enum': ['natural', 'vivid']
        }
    }
    required_arguments = ['prompt']
    
    def __call__(self, prompt, quality='standard', size='1024x1024',
                 style='natural'):
        from openai import OpenAI
        logger.info(f'generating image: {prompt}, quality={quality}, '
                    f'size={size}, style={style}')
        client = OpenAI(api_key=config.openai_api_key)
        response = client.images.generate(model='dall-e-3', prompt=prompt,
                                          size=size, quality=quality,
                                          style=style,
                                          response_format='b64_json', n=1)
        data = response.data[0].b64_json
        html = f'Here\'s an image for "{prompt}"!\n<div class="image-generation mask"><img src="data:image/png;base64,{data}"></div>'
        return html, None, False
