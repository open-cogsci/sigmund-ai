from langchain.schema import SystemMessage, HumanMessage, AIMessage
from heymans.utils import prepare_messages


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
