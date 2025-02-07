from langchain.schema import SystemMessage, HumanMessage, AIMessage
from sigmund.utils import prepare_messages, extract_workspace, \
    remove_masked_elements, process_ai_message, dedent_code_blocks, \
    fix_markdown_headings, fix_bullet_points


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


def test_fix_markdown_headings():
    """
    Runs assertion-based tests on the fix_markdown_headings function.
    """

    test_cases = [
        {
            "name": "Box drawing characters around a normal heading",
            "input": """────────────────────────────────────
Heading 1
────────────────────────────────────
This is some text after heading 1.
""",
            "expected": """## Heading 1

This is some text after heading 1.

"""
        },
        {
            "name": "Dashed lines around heading",
            "input": """-----------------------
Second Heading
-----------------------
Some more text follows here.
""",
            "expected": """## Second Heading

Some more text follows here.

"""
        },
        {
            "name": "A blank heading (should NOT convert)",
            "input": """────────────────

────────────────
We had blank lines.
""",
            "expected": """────────────────

────────────────
We had blank lines.

"""
        },
        {
            "name": "No rule lines at all",
            "input": """Just a piece of text.
No headings here whatsoever.
""",
            "expected": """Just a piece of text.
No headings here whatsoever.

"""
        },
        {
            "name": "Multiple headings in succession",
            "input": """────────────────────────
Heading A
────────────────────────
Text under heading A.

-----------------------
Heading B
-----------------------
Text under heading B.
""",
            "expected": """## Heading A

Text under heading A.

## Heading B

Text under heading B.

"""
        },
        {
            "name": "Heading followed by more dash lines (should only use pairs)",
            "input": """-----------------------
Misinterpreted?
-----------------------
-----------------------
Real Heading
-----------------------
More text.
""",
            "expected": """## Misinterpreted?

## Real Heading

More text.

"""
        }
    ]
    
    for case in test_cases:
        result = fix_markdown_headings(case["input"])
        assert result.rstrip() == case["expected"].rstrip(), (
            f"Test '{case['name']}' failed.\n"
            f"Expected:\n{repr(case['expected'])}\n"
            f"Got:\n{repr(result)}"
        )
    
    print("All tests passed!")


def test_fix_bullet_points():
    # 1) A line that starts with '• ' becomes '- '
    input_text = "• This is a bullet.\nSome other line.\n• Another bullet."
    expected = "- This is a bullet.\nSome other line.\n- Another bullet."
    output = fix_bullet_points(input_text)
    assert output == expected, f"1) Expected:\n{expected}\nGot:\n{output}"
    
    # 2) A line that has '•' not at the start but in the middle of text remains unchanged
    input_text = "Some line with a • in the middle."
    expected = "Some line with a • in the middle."
    output = fix_bullet_points(input_text)
    assert output == expected, f"2) Expected:\n{expected}\nGot:\n{output}"
    
    # 3) No bullets
    input_text = "No special bullet points here."
    expected = "No special bullet points here."
    output = fix_bullet_points(input_text)
    assert output == expected, f"3) Expected:\n{expected}\nGot:\n{output}"
    
    # 4) Mixed lines
    input_text = "• bullet\nplain line\n• bullet again\n"
    expected = "- bullet\nplain line\n- bullet again\n"
    output = fix_bullet_points(input_text)
    assert output == expected, f"4) Expected:\n{expected}\nGot:\n{output}"
    
    print("All tests for fix_bullet_points passed!")
