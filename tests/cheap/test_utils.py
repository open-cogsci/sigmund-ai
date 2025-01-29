from langchain.schema import SystemMessage, HumanMessage, AIMessage
from sigmund.utils import prepare_messages, extract_workspace, \
    remove_masked_elements, process_ai_message, dedent_code_blocks


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


def test_process_ai_message():
    test_case = '''# Header should go to next line

Enumerations should be fixed:
- one line
- another line

The following should be dedented:

    ```
    def test():
        pass
    ```

This as well:

	```python
	def test():
	    pass
	```

  ~~~
  def test():
      pass
  ~~~

And this as well:

		~~~python
		def test():
		    pass
		~~~

But not this (because it's not uniformly indented): 

    ```
def test():
    pass
```

'''

    expected_output = '''

# Header should go to next line

Enumerations should be fixed:

- one line
- another line

The following should be dedented:

```
def test():
    pass
```

This as well:

```python
def test():
    pass
```

~~~
def test():
    pass
~~~

And this as well:

~~~python
def test():
    pass
~~~

But not this (because it's not uniformly indented): 

    ```
def test():
    pass
```

'''
    actual_output = process_ai_message(test_case)    
    assert expected_output == actual_output


def test_dedent_code_blocks():
    
        test_cases = [
            (
                "No code blocks",
                "Just a line of text\nAnd another line\n",
                "Just a line of text\nAnd another line\n"
            ),
            (
                "Already unindented code block with triple backticks",
                """```
some code
```""",
                """```
some code
```"""
            ),
            (
                "Simple uniformly-indented code block with triple backticks",
                """    ```\n    print("Hello World")\n    ```""",
                """```
print("Hello World")
```"""
            ),
            (
                "Triple-tilde code block with uniform indentation",
                """        ~~~
        a = 1
        b = 2
        ~~~""",
                """~~~
a = 1
b = 2
~~~"""
            ),
            (
                "Non-uniform indentation, should remain unchanged",
                """    ```
        print("Hello")
    ```""",
                """    ```
        print("Hello")
    ```"""
            ),
            (
                "Block missing ending fence, should remain unchanged",
                """    ```
    print("No closing fence")
                """,
                """    ```
    print("No closing fence")
                """
            ),
            (
                "Content that almost looks like a code block but isn't (leading spaces then backticks mid-line)",
                """    This is a line with ```backticks``` in the middle
    But not a real code fence
    """,
                """    This is a line with ```backticks``` in the middle
    But not a real code fence
    """
            ),
            (
                "Multiple code blocks in the same text",
                """Some text here
    ```
    block1
    ```
Some more text
        ~~~
        block2
        ~~~
Done""",
                """Some text here
```
block1
```
Some more text
~~~
block2
~~~
Done"""
            ),
        ]

        for desc, input_text, expected in test_cases:
            print(desc)
            dedent_code_blocks(input_text) == expected
