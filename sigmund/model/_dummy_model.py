from ._base_model import BaseModel


class DummyModel(BaseModel):
    
    def get_response(self, response):
        return response
    
    def invoke(self, messages):
        return '''dummy reply
        
<p>This is a paragraph with some <code><p>example</p></code></p>

```css
<style>
p { color: purple!important }
</style>
```
'''

    async def _async_task(self):
        return 'dummy reply'

    def async_invoke(self, messages):
        import asyncio
        return asyncio.create_task(self._async_task())
