from sigmund.process_sigmund_message import process_ai_message, dedent_code_blocks, \
    fix_markdown_headings, normalize_bullet_points, replace_round_bracket_with_dot, fix_indentation_after_colon, \
    add_blank_line_after_colon_headers, fix_list_formatting_1, fix_list_formatting_2, \
    fix_list_formatting_3, fix_list_formatting_4, fix_list_formatting_5, fix_list_formatting_6, \
    fix_list_formatting_7, fix_list_formatting_8, fix_list_formatting_9, \
    fix_list_formatting_10, fix_list_formatting_11, fix_list_formatting_12, \
    escape_html_tags

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

def test_normalize_bullet_points():
    # A line that starts with • should start with - instead
    input_text = '• This is a test'
    expected = '- This is a test'
    output = normalize_bullet_points(input_text)
    assert output == expected

    # A line that starts with – should start with - instead
    input_text = '– This is a test'
    expected = '- This is a test'
    output = normalize_bullet_points(input_text)
    assert output == expected

    # A line that starts with ' ♦' should start with ' -' instead
    input_text = ' ♦ This is a test'
    expected = ' - This is a test'
    output = normalize_bullet_points(input_text)
    assert output == expected

    # A line that starts with '  ○' should start with '  -' instead
    input_text = '  ○ This is a test'
    expected = '  - This is a test'
    output = normalize_bullet_points(input_text)
    assert output == expected

    # A line that starts with '  •' should NOT start with '-' instead
    input_text = '  • This is a test'
    expected = '- This is a test'
    output = normalize_bullet_points(input_text)
    assert output != expected

def test_add_blank_line_after_colon_headers():
    # A text like this should be followed by a blank line
    input_text = """This is a list:
- point 1
- point 2
- point 3"""
    expected = """This is a list:

- point 1
- point 2
- point 3"""
    output = add_blank_line_after_colon_headers(input_text)
    assert output == expected
    
    # A text like this should be followed by a blank line
    input_text = """This is a list
- point 1
- point 2
- point 3"""
    expected = """This is a list

- point 1
- point 2
- point 3"""
    output = add_blank_line_after_colon_headers(input_text)
    assert output == expected

    # A text like this should be followed by a blank line
    input_text = """**This is a list:**
- point 1
- point 2
- point 3"""
    expected = """**This is a list:**

- point 1
- point 2
- point 3"""
    output = add_blank_line_after_colon_headers(input_text)
    assert output == expected

    # A text like this should also be followed by a blank line
    input_text = """This is a list:
- point 1
    - point 2
    - point 3"""
    expected = """This is a list:

- point 1
    - point 2
    - point 3"""
    output = add_blank_line_after_colon_headers(input_text)
    assert output == expected

    # A text like this should NOT be followed by a blank line because we are already in a list
    input_text = """- This is a list:
        - point 1
        - point 2
        - point 3"""
    expected = """- This is a list:
        - point 1
        - point 2
        - point 3"""
    output = add_blank_line_after_colon_headers(input_text)
    assert output == expected

# Between 1 and 3 spaces before hyphen at the start of a row should become 4 spaces - this is the correct number of spaces for a second level markdown list
def test_fix_list_formatting_1():
    input_text = ' - This is a test'
    expected = '    - This is a test'
    output = fix_list_formatting_1(input_text)
    assert output == expected

    #It should NOT adjust 5 leading spaces
    input_text = '     - This is a test'
    expected = '     - This is a test'
    output = fix_list_formatting_1(input_text)
    assert output == expected

def test_fix_list_formatting_2():
    input_text = '  - This is a test'
    expected = '    - This is a test'
    output = fix_list_formatting_2(input_text)
    assert output == expected

    #It should NOT adjust 5 leading spaces
    input_text = '     - This is a test'
    expected = '     - This is a test'
    output = fix_list_formatting_2(input_text)
    assert output == expected

def test_fix_list_formatting_3():
    input_text = '   - This is a test'
    expected = '    - This is a test'
    output = fix_list_formatting_3(input_text)
    assert output == expected

    #It should NOT adjust 5 leading spaces
    input_text = '     - This is a test'
    expected = '     - This is a test'
    output = fix_list_formatting_3(input_text)
    assert output == expected

# Between 5 and 7 spaces before hyphen at the start of a row should become 8 spaces - this is the correct number of spaces for a third level markdown list
def test_fix_list_formatting_4():
    input_text = '     - This is a test'
    expected = '        - This is a test'
    output = fix_list_formatting_4(input_text)
    assert output == expected

    #It should NOT adjust 2 leading spaces
    input_text = '  - This is a test'
    expected = '  - This is a test'
    output = fix_list_formatting_4(input_text)
    assert output == expected

def test_fix_list_formatting_5():
    input_text = '      - This is a test'
    expected = '        - This is a test'
    output = fix_list_formatting_5(input_text)
    assert output == expected

    #It should NOT adjust 2 leading spaces
    input_text = '  - This is a test'
    expected = '  - This is a test'
    output = fix_list_formatting_5(input_text)
    assert output == expected

def test_fix_list_formatting_6():
    input_text = '       - This is a test'
    expected = '        - This is a test'
    output = fix_list_formatting_6(input_text)
    assert output == expected

    #It should NOT adjust 2 leading spaces
    input_text = '  - This is a test'
    expected = '  - This is a test'
    output = fix_list_formatting_6(input_text)
    assert output == expected

#Sometimes lines start with '1)'. The correct markdown format is '1.'. 
def test_replace_round_bracket_with_dot():
    input_text = '1) This is a test'
    expected = '1. This is a test'
    output = replace_round_bracket_with_dot(input_text)
    assert output == expected

    input_text = '   1) This is a test'
    expected = '   1. This is a test'
    output = replace_round_bracket_with_dot(input_text)
    assert output == expected
    
    #It should NOT delete any spaces
    input_text = '  1) This is a test'
    expected = '1. This is a test'
    output = fix_list_formatting_6(input_text)
    assert output != expected

# Between 1 and 3 spaces before ordinal list at the start of a row should become 4 spaces - this is the correct number of spaces for a second level markdown list
def test_fix_list_formatting_7():
    input_text = ' 1. This is a test'
    expected = '    1. This is a test'
    output = fix_list_formatting_7(input_text)
    assert output == expected

    #It should NOT adjust 5 leading spaces
    input_text = '     4. This is a test'
    expected = '     4. This is a test'
    output = fix_list_formatting_7(input_text)
    assert output == expected

def test_fix_list_formatting_8():
    input_text = '  2. This is a test'
    expected = '    2. This is a test'
    output = fix_list_formatting_8(input_text)
    assert output == expected

    #It should NOT adjust 5 leading spaces
    input_text = '     1. This is a test'
    expected = '     1. This is a test'
    output = fix_list_formatting_8(input_text)
    assert output == expected

def test_fix_list_formatting_9():
    input_text = '   3. This is a test'
    expected = '    3. This is a test'
    output = fix_list_formatting_9(input_text)
    assert output == expected

    #It should NOT adjust 5 leading spaces
    input_text = '     6. This is a test'
    expected = '     6. This is a test'
    output = fix_list_formatting_9(input_text)
    assert output == expected

# Between 5 and 7 spaces before ordinal list at the start of a row should become 4 spaces - this is the correct number of spaces for a third level markdown list
def test_fix_list_formatting_10():
    input_text = '     1. This is a test'
    expected = '        1. This is a test'
    output = fix_list_formatting_10(input_text)
    assert output == expected

    #It should NOT adjust 2 leading spaces
    input_text = '  1. This is a test'
    expected = '  1. This is a test'
    output = fix_list_formatting_10(input_text)
    assert output == expected

def test_fix_list_formatting_11():
    input_text = '      1. This is a test'
    expected = '        1. This is a test'
    output = fix_list_formatting_11(input_text)
    assert output == expected

    #It should NOT adjust 2 leading spaces
    input_text = '  1. This is a test'
    expected = '  1. This is a test'
    output = fix_list_formatting_11(input_text)
    assert output == expected

def test_fix_list_formatting_12():
    input_text = '       1. This is a test'
    expected = '        1. This is a test'
    output = fix_list_formatting_12(input_text)
    assert output == expected

    #It should NOT adjust 2 leading spaces
    input_text = '  1. This is a test'
    expected = '  1. This is a test'
    output = fix_list_formatting_12(input_text)
    assert output == expected

def test_fix_indentation_after_colon():
    
    #Should not crash when last row in the text ends with a colon
    input_text = """This will be the last row of the text:"""
    expected = """This will be the last row of the text:"""
    output = fix_indentation_after_colon(input_text)
    assert output == expected
    
    #Should dedent lists, so it is formatted correctly after
    input_text = """This will be a list:
        - point 1
            - point 2
            - point 3"""
    expected = """This will be a list:
- point 1
    - point 2
    - point 3"""
    output = fix_indentation_after_colon(input_text)
    assert output == expected

    #second test
    input_text = """This will be a list:
        - point 1
        - point 2
        - point 3"""
    expected = """This will be a list:
- point 1
- point 2
- point 3"""
    output = fix_indentation_after_colon(input_text)
    assert output == expected

    #third test - it should NOT change indentation if its already part of a list
    input_text = """1. This will be a list:
        - point 1
            - point 2
            - point 3"""
    expected = """1. This will be a list:
        - point 1
            - point 2
            - point 3"""
    output = fix_indentation_after_colon(input_text)
    assert output == expected

def test_process_ai_message():
    test_case_1 = '''# Header should go to next line

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

    expected_output_1 = '''

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
    actual_output_1 = process_ai_message(test_case_1)    
    assert expected_output_1 == actual_output_1

    test_case_2 = """Step-by-Step Guide to Create a Basic Experiment in OpenSesame

4) **Design Trial Sequence**:
   • Within `trial_sequence`, add various items representing different parts of each trial:
     • **Sketchpad**: For displaying visual stimuli.
     • **Keyboard or Mouse Response**: For collecting participant responses.
     • Optionally, **inline_script**: For custom Python scripting if needed."""
    
    expected_output_2 = """Step-by-Step Guide to Create a Basic Experiment in OpenSesame

4. **Design Trial Sequence**:
    - Within `trial_sequence`, add various items representing different parts of each trial:
        - **Sketchpad**: For displaying visual stimuli.
        - **Keyboard or Mouse Response**: For collecting participant responses.
        - Optionally, **inline_script**: For custom Python scripting if needed."""
    
    actual_output_2 = process_ai_message(test_case_2)    
    assert expected_output_2 == actual_output_2

    test_case_3 = """Step-by-Step Guide to Create a Basic Experiment in OpenSesame:
    • Within `trial_sequence`, add various items representing different parts of each trial:
        • **Sketchpad**: For displaying visual stimuli.
        • **Keyboard or Mouse Response**: For collecting participant responses.
        • Optionally, **inline_script**: For custom Python scripting if needed."""
    
    expected_output_3 = """Step-by-Step Guide to Create a Basic Experiment in OpenSesame:

- Within `trial_sequence`, add various items representing different parts of each trial:
    - **Sketchpad**: For displaying visual stimuli.
    - **Keyboard or Mouse Response**: For collecting participant responses.
    - Optionally, **inline_script**: For custom Python scripting if needed."""

    actual_output_3 = process_ai_message(test_case_3)    
    assert expected_output_3 == actual_output_3


def test_escape_html_tags():
    # Test 1: Basic HTML escaping (no code blocks)
    assert escape_html_tags("<div>Hello</div>") == "&lt;div&gt;Hello&lt;/div&gt;"
    assert escape_html_tags("Use <br> for line breaks") == "Use &lt;br&gt; for line breaks"
    
    # Test 2: Text with no HTML tags
    assert escape_html_tags("Just plain text") == "Just plain text"
    
    # Test 3: Code block with ``` (no language)
    text = "Here's some code:\n```\n<div>Not escaped</div>\n```"
    expected = "Here's some code:\n```\n<div>Not escaped</div>\n```"
    assert escape_html_tags(text) == expected
    
    # Test 4: Code block with ``` and language
    text = "HTML example:\n```html\n<p>Paragraph</p>\n```"
    expected = "HTML example:\n```html\n<p>Paragraph</p>\n```"
    assert escape_html_tags(text) == expected
    
    # Test 5: Code block with ~~~
    text = "Code:\n~~~\n<tag>Content</tag>\n~~~"
    expected = "Code:\n~~~\n<tag>Content</tag>\n~~~"
    assert escape_html_tags(text) == expected
    
    # Test 6: Code block with ~~~ and language
    text = "Python:\n~~~python\ndef func():\n    return '<value>'\n~~~"
    expected = "Python:\n~~~python\ndef func():\n    return '<value>'\n~~~"
    assert escape_html_tags(text) == expected
    
    # Test 7: Mixed content
    text = """<p>This should be escaped</p>
```javascript
<script>alert('Not escaped')</script>
```
<div>Also escaped</div>"""
    expected = """&lt;p&gt;This should be escaped&lt;/p&gt;
```javascript
<script>alert('Not escaped')</script>
```
&lt;div&gt;Also escaped&lt;/div&gt;"""
    assert escape_html_tags(text) == expected
    
    # Test 8: Multiple code blocks
    text = """<tag1>Escape this</tag1>
```
<keep>This</keep>
```
<tag2>And this</tag2>
~~~html
<preserve>This too</preserve>
~~~
<tag3>But not this</tag3>"""
    expected = """&lt;tag1&gt;Escape this&lt;/tag1&gt;
```
<keep>This</keep>
```
&lt;tag2&gt;And this&lt;/tag2&gt;
~~~html
<preserve>This too</preserve>
~~~
&lt;tag3&gt;But not this&lt;/tag3&gt;"""
    assert escape_html_tags(text) == expected
    
    # Test 9: Empty code blocks
    text = "Before\n```\n```\nAfter <tag>"
    expected = "Before\n```\n```\nAfter &lt;tag&gt;"
    assert escape_html_tags(text) == expected
    
    # Test 10: Code block at start/end of text
    text = "```\n<code>Here</code>\n```\n<outside>This</outside>"
    expected = "```\n<code>Here</code>\n```\n&lt;outside&gt;This&lt;/outside&gt;"
    assert escape_html_tags(text) == expected
    
    print("All tests passed! ✅")
    
# -------------------------
# Pytest-style test cases
# -------------------------

def test_escapes_basic_html():
    message = '<p>Hello & welcome</p>'
    expected = '&lt;p&gt;Hello &amp; welcome&lt;/p&gt;'
    assert escape_html_tags(message) == expected

def test_preserves_allowed_div_thinking_block_signature():
    message = 'before <em>z</em> <div class="thinking_block_signature"><b>Hi & bye</b></div> after'
    expected = 'before &lt;em&gt;z&lt;/em&gt; <div class="thinking_block_signature"><b>Hi & bye</b></div> after'
    assert escape_html_tags(message) == expected

def test_preserves_allowed_div_with_additional_classes_and_attrs():
    message = '<div id="x" class="foo message-info bar" data-x="1">Hello <i>World</i> & ok</div>'
    expected = message
    assert escape_html_tags(message) == expected

def test_preserves_message_info_with_markdown_attr():
    message = '<div class="message-info" markdown="1">A & B <span>C</span></div>'
    expected = message
    assert escape_html_tags(message) == expected

def test_does_not_preserve_non_div_even_with_class():
    message = '<span class="message-info">X & Y</span>'
    expected = '&lt;span class="message-info"&gt;X &amp; Y&lt;/span&gt;'
    assert escape_html_tags(message) == expected

def test_preserves_code_blocks_triple_backticks_with_lang():
    message = 'Start <b>1</b>\n```python\n<p>& stuff</p>\n```\nEnd <i>2</i>'
    expected = 'Start &lt;b&gt;1&lt;/b&gt;\n```python\n<p>& stuff</p>\n```\nEnd &lt;i&gt;2&lt;/i&gt;'
    assert escape_html_tags(message) == expected

def test_preserves_code_blocks_tildes():
    message = '~~~\n<a>&</a>\n~~~'
    expected = '~~~\n<a>&</a>\n~~~'
    assert escape_html_tags(message) == expected

def test_mixed_content_properly_escaped_and_preserved():
    message = (
        '<h1>T</h1>\n'
        '<div class="thinking_block_content">A & <span>B</span></div>\n'
        '```js\n<div>not escaped here</div>&\n```\n'
        '<div class="foo">bar & baz</div>\n'
    )
    expected = (
        '&lt;h1&gt;T&lt;/h1&gt;\n'
        '<div class="thinking_block_content">A & <span>B</span></div>\n'
        '```js\n<div>not escaped here</div>&\n```\n'
        '&lt;div class="foo"&gt;bar &amp; baz&lt;/div&gt;\n'
    )
    assert escape_html_tags(message) == expected

def test_partial_class_name_is_not_preserved():
    message = '<div class="thinking_block_signature_extra">X & Y</div>'
    expected = '&lt;div class="thinking_block_signature_extra"&gt;X &amp; Y&lt;/div&gt;'
    assert escape_html_tags(message) == expected

def test_case_insensitive_matching_for_div_and_class():
    message = '<DIV CLASS="MESSAGE-INFO">X & Y</DIV>'
    expected = message
    assert escape_html_tags(message) == expected

def test_class_attribute_order_does_not_matter():
    message = '<div data-foo="1" class="foo thinking_block_content">Z & Q</div>'
    expected = message
    assert escape_html_tags(message) == expected    
