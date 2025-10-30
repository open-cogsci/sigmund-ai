from sigmund.utils import prepare_messages, extract_workspace, remove_masked_elements


def test_prepare_messages():
    # Test Case 1: Empty list of messages
    messages = []
    assert prepare_messages(messages) == []

    # Test Case 2: Single message
    messages = [dict(role="system", content="System message")]
    assert prepare_messages(messages) == messages

    # Test Case 3: First AI message not allowed
    messages = [
        dict(role="system", content="System message"),
        dict(role="assistant", content="AI message"),
        dict(role="user", content="Human message")
    ]
    expected_output = [
        dict(role="system", content="System message"),
        dict(role="user", content="Human message")
    ]
    assert prepare_messages(messages, allow_ai_first=False) == expected_output

    # Test Case 4: Last AI message not allowed
    messages = [
        dict(role="system", content="System message"),
        dict(role="user", content="Human message"),
        dict(role="assistant", content="AI message")
    ]
    expected_output = [
        dict(role="system", content="System message"),
        dict(role="user", content="Human message"),
        dict(role="assistant", content="AI message"),
        dict(role="user", content="Please continue!")
    ]
    assert prepare_messages(messages, allow_ai_last=False) == expected_output

    # Test Case 5: Merge consecutive messages
    messages = [
        dict(role="system", content="System message"),
        dict(role="user", content="Human message 1"),
        dict(role="user", content="Human message 2"),
        dict(role="assistant", content="AI message 1"),
        dict(role="assistant", content="AI message 2")
    ]
    expected_output = [
        dict(role="system", content="System message"),
        dict(role="user", content="Human message 1\nHuman message 2"),
        dict(role="assistant", content="AI message 1\nAI message 2")
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
    s = '''Here's a simple workspace example with a missing newline before closing tag:
    
<workspace language="javascript">
console.log('hello world')</workspace>'''
    txt, content, language = extract_workspace(s)
    assert txt.strip() == "Here's a simple workspace example with a missing newline before closing tag:"
    assert content.strip() == "console.log('hello world')"
    assert language == 'javascript'
    s = '''Here's a double workspace example:

<workspace language="python">
print('hello world')
</workspace>

And a second workspace:

<workspace language="python">
print('hello again world')
</workspace>

And a third workspace:

<workspace>
print('hello yet again world')
</workspace>
'''
    txt, content, language = extract_workspace(s)
    assert txt.strip() == '''Here's a double workspace example:



And a second workspace:

```python
print('hello again world')
```

And a third workspace:

```markdown
print('hello yet again world')
```'''
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
