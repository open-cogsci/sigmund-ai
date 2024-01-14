from heymans.tools import BaseTool, CodeExcutionTool, GoogleScholarTool


def test_tools_json():
    
    class TestTool(BaseTool):
        json_pattern = CodeExcutionTool.json_pattern
        def use(self, message, language, code):
            return '', False
    
    tool = TestTool(None)
    
    target = 'Some text'
    message = '''Some text

{
    "execute_code":
        {
            "language": "python",
            "code": "pass"
        }
}'''
    target_message, results, needs_reply = tool.run(message)
    assert target_message.strip() == target
    message = '''Some text

```json
{
    "execute_code":
        {
            "language": "python",
            "code": "pass"
        }
}
```
'''
    target_message, results, needs_reply = tool.run(message)
    assert target_message.strip() == target
    target = 'Running `TestTool` … <TRANSIENT>'
    message = '''{
    "execute_code":
        {
            "language": "python",
            "code": "pass"
        }
}'''
    target_message, results, needs_reply = tool.run(message)
    assert target_message.strip() == target
    
    class TestTool(BaseTool):
        json_pattern = GoogleScholarTool.json_pattern
        def use(self, message, queries):
            return '', False
    
    tool = TestTool(None)
    message = '''Sure, I can help you find articles that are related to your manuscript's topic. This might provide us with authors who have recently published in this field, and they could be potential reviewers for your manuscript. Let's perform a search on Google Scholar to find such articles.

Please wait a moment while I perform the search.

{ "search_google_scholar": [ "Open-Access Database of Video Stimuli for Action Observation", "Psychometric Evaluation in Neuroimaging", "Motion Characterization in Neuroimaging Settings" ] }'''
    target_message, results, needs_reply = tool.run(message)
    assert target_message.strip() == '''Sure, I can help you find articles that are related to your manuscript's topic. This might provide us with authors who have recently published in this field, and they could be potential reviewers for your manuscript. Let's perform a search on Google Scholar to find such articles.

Please wait a moment while I perform the search.'''
    message = '''Sure, I can help with that. I'll perform a search on Google Scholar for articles related to pupil size. Just a moment, please. 

```json
{
    "search_google_scholar": [
        "pupil size"
    ]
}
```
'''
    target_message, results, needs_reply = tool.run(message)
    assert target_message.strip() == '''Sure, I can help with that. I'll perform a search on Google Scholar for articles related to pupil size. Just a moment, please.'''
