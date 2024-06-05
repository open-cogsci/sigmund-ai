I would like the fixation dot to turn green when the participant gives the correct response and to turn red when the participant gives the incorrect response. How can I do that without using an inline script?

The answer should:

- Define correct response by defining the correct_response variable in a LOOP table
- Collect a response with a keyboard_response item
- After the keyboard_response item, insert a feedback item
- Draw a green fixation dot in the feedback item and use the show-if expression `correct == 1` to indicate that it should be shown when the response is correct
- Draw a red fixation dot in the feedback item and use the show-if expression `correct == 0` to indicate that it should be shown when the response is incorrect

Alternative solutions:

- Instead of using a feedback item, you can also use two sketchpad items, one with a green and one with a red fixation dot, and show only one of them using a run-if expression

The answer should not:

- Use a Python inline_script item
- Use an inline_javascript item
- Use show-if or run-if expressions using square brackets, that is: `[correct] = 1` is not a valid expression, but `correct == 1` is.