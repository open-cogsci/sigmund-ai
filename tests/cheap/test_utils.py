from langchain.schema import SystemMessage, HumanMessage, AIMessage
from sigmund.utils import prepare_messages, extract_workspace, remove_masked_elements


def test_prepare_messages():
    # Test Case 1: Empty list of messages
    messages = []
    assert prepare_messages(messages) == []

    # Test Case 2: Single message
    messages = [SystemMessage(content="System message")]
    assert prepare_messages(messages) == messages

    # Test Case 3: First AI message not allowed
    messages = [
        SystemMessage(content="System message"),
        AIMessage(content="AI message"),
        HumanMessage(content="Human message")
    ]
    expected_output = [
        SystemMessage(content="System message"),
        HumanMessage(content="Human message")
    ]
    assert prepare_messages(messages, allow_ai_first=False) == expected_output

    # Test Case 4: Last AI message not allowed
    messages = [
        SystemMessage(content="System message"),
        HumanMessage(content="Human message"),
        AIMessage(content="AI message")
    ]
    expected_output = [
        SystemMessage(content="System message"),
        HumanMessage(content="Human message"),
        AIMessage(content="AI message"),
        HumanMessage(content="Please continue!")
    ]
    assert prepare_messages(messages, allow_ai_last=False) == expected_output

    # Test Case 5: Merge consecutive messages
    messages = [
        SystemMessage(content="System message"),
        HumanMessage(content="Human message 1"),
        HumanMessage(content="Human message 2"),
        AIMessage(content="AI message 1"),
        AIMessage(content="AI message 2")
    ]
    expected_output = [
        SystemMessage(content="System message"),
        HumanMessage(content="Human message 1\nHuman message 2"),
        AIMessage(content="AI message 1\nAI message 2")
    ]
    assert prepare_messages(messages, merge_consecutive=True) == expected_output
    
    
def test_extract_workspace():
    
    s = '''Here's a simple workspace example:
    
<workspace language="python">
print('hello world')
</workspace>'''
    txt, content, language = extract_workspace(s)
    assert txt.strip() == "Here's a simple workspace example:"
    assert content.strip() == "print('hello world')"
    assert language == 'python'
    s = '''Here's a simple workspace example:
    
```python
print(1)
print(2)
print(3)
```
'''
    txt, content, language = extract_workspace(s)
    assert s == txt
    assert content.strip() == "print(1)\nprint(2)\nprint(3)"
    assert language == 'python'
    s = '''Here's a simple workspace example:
    
```python
print(1)
```
'''
    txt, content, language = extract_workspace(s)
    assert s == txt
    assert content is None
    assert language is None
    s = '''Here's a simple workspace example:
    
<workspace>
print('hello world')
</workspace>'''
    txt, content, language = extract_workspace(s)
    assert txt.strip() == "Here's a simple workspace example:"
    assert content.strip() == "print('hello world')"
    assert language == 'markdown'
    s = '''Here's a simple workspace example:
    
```
print(1)
print(2)
print(3)
```
'''
    txt, content, language = extract_workspace(s)
    assert s == txt
    assert content.strip() == "print(1)\nprint(2)\nprint(3)"
    assert language == 'markdown'
    s = '''Here's a simple workspace example:
    
```
print(1)
```
'''
    txt, content, language = extract_workspace(s)
    assert s == txt
    assert content is None
    assert language is None
    
    
def test_remove_masked_elements():
    html_content = """
    Here's some content
    
    <div class="test mask">
    This should be masked
    </div>
    
    And more content
    
    <div class="test">
    This should not be masked
    </div>
    
    And more
    
    <span class="mask">
    This should not be masked
    </span>
    """
    
    expected_output = """
    Here's some content
    
    
    
    And more content
    
    <div class="test">
    This should not be masked
    </div>
    
    And more
    """
    
    result = remove_masked_elements(html_content)
    assert result.strip() == expected_output.strip()
