I would like to use a Python script to collect a mouse click press. I would like the mouse cursor to be visible. There should be response timeout of five seconds. Can you show me how?

The answer should:

- Refer to a Python inline_script
- Indicate that the mouse should be prepared in the prepare phase and used to collect a response in the run phase
- In the prepare phase: Initialize a mouse with an uppercase function: `my_mouse = Mouse()`. The name of the keyboard can be anything and doesn't need to be `my_mouse`.
- In the run phase: Collect a keyboard with `button, pos, t = my_mouse.get_click(timeout=500, visible=True)`
- The `timeout` and `visible` parameters can also be passed during initialization: `my_mouse = Mouse(timeout=2000, visible=True)`

The answer should not not:

- Refer to a `mouse_response` item
- Use JavaScript
- Initialize the mouse with a lowercase function
- Pass `exp` as argument when initializing the mouse
