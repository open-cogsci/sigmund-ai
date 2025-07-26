from ._base_model import BaseModel


class DummyModel(BaseModel):
    
    def get_response(self, response):
        return response
    
    def invoke(self, messages):
        return '''<div class="thinking_block_signature">thinking_signature</div><div class="thinking_block_content">thinking_content</div> 
        
        
dummy reply
        
<p>This is a paragraph with some <code><p>example</p></code></p>

```css
<style>
p { color: purple!important }
</style>
```

```js
<script>
alert("This is a codeblock example script that should not be executed")
</script>
```

<script>
alert("This is message example script that should not be executed")
</script>

<workspace>
<script>
alert("This is workspace script that should not be executed")
</script>
</workspace>
'''

    async def _async_task(self):
        return 'dummy reply'

    def async_invoke(self, messages):
        import asyncio
        return asyncio.create_task(self._async_task())
