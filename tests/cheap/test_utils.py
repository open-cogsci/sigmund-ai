from sigmund.utils import prepare_messages, remove_masked_elements


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
