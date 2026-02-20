from . import BaseTool
import logging
import time
import base64
import requests
from .. import config
logger = logging.getLogger('sigmund')


class generate_image_flux(BaseTool):
    """Generate or edit an image based on a text description using Flux 2.
    When one or more images are attached by the user, they are used as
    reference images for editing.
    """

    arguments = {
        'prompt': {
            'type': 'string',
            'description': 'The image description or edit instruction.'
        },
        'model': {
            'type': 'string',
            'description': 'The Flux model to use. Default: flux-2-pro.',
            'enum': ['flux-2-pro', 'flux-2-max']
        },
        'width': {
            'type': 'integer',
            'description': 'Output width in pixels. Must be a multiple of '
                           '16. Default: 1024.',
        },
        'height': {
            'type': 'integer',
            'description': 'Output height in pixels. Must be a multiple of '
                           '16. Default: 1024.',
        },
        'steps': {
            'type': 'integer',
            'description': 'Number of inference steps. Maximum: 50. '
                           'Default: 50.',
        },
        'guidance': {
            'type': 'number',
            'description': 'Guidance scale controlling how closely the '
                           'output follows the prompt. Minimum: 1.5, '
                           'maximum: 10. Default: 4.5.',
        }
    }
    required_arguments = ['prompt']

    def __call__(self, prompt, model='flux-2-pro', width=1024, height=1024,
                 steps=50, guidance=4.5):
        logger.info(f'generating image: {prompt}, model={model}, '
                    f'width={width}, height={height}, steps={steps}, '
                    f'guidance={guidance}')
        payload = {
            'prompt': prompt,
            'width': int(width),
            'height': int(height),
            'steps': int(steps),
            'guidance': float(guidance),
            'safety_tolerance': 5,
            'output_format': 'png',
        }
        # Attach reference images
        image_attachments = [
            a for a in (self._attachments or [])
            if a.get('type') == 'image'
        ][:8]
        for i, attachment in enumerate(image_attachments):
            url = attachment['url']
            # Extract raw base64 from data URL if needed
            if url.startswith('data:'):
                b64_data = url.split(',', 1)[1]
            else:
                b64_data = url
            key = 'input_image' if i == 0 else f'input_image_{i + 1}'
            payload[key] = b64_data
        # Submit the generation request
        api_url = f'https://api.bfl.ai/v1/{model}'
        response = requests.post(
            api_url,
            headers={
                'accept': 'application/json',
                'x-key': config.bfl_api_key,
                'Content-Type': 'application/json',
            },
            json=payload,
        )
        response.raise_for_status()
        response_data = response.json()
        request_id = response_data.get('id')
        polling_url = response_data.get('polling_url')
        if not request_id or not polling_url:
            logger.error(f'Failed to submit image generation: '
                         f'{response_data}')
            return ('Failed to generate image. Please try again.',
                    None, False)
        # Poll for result (up to ~60 seconds)
        for _ in range(300):
            time.sleep(0.5)
            result = requests.get(
                polling_url,
                headers={
                    'accept': 'application/json',
                    'x-key': config.bfl_api_key,
                },
                params={'id': request_id},
            ).json()
            if result['status'] == 'Ready':
                image_url = result['result']['sample']
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                image_b64 = base64.b64encode(
                    image_response.content).decode('utf-8')
                html = (
                    f'Here\'s an image for "{prompt}"!\n'
                    f'<div class="image-generation mask">'
                    f'<img src="data:image/png;base64,{image_b64}">'
                    f'</div>'
                )
                return html, None, False
            elif result['status'] in ['Error', 'Failed']:
                logger.error(f'Image generation failed: {result}')
                return ('Failed to generate image. Please try again.',
                        None, False)
        logger.error('Image generation timed out')
        return 'Image generation timed out. Please try again.', None, False
