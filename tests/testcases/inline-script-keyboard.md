I would like to use a Python script to collect a key press. I only want to accept 'q' and 'p' keys. There should be response timeout of two seconds.

The answer should:

- Refer to a Python inline_script
- Indicate that the keyboard should be prepared in the prepare phase and used to collect a response in the run phase
- In the prepare phase: Initialize a keyboard with an uppercase function: `my_keyboard = Keyboard()`. The name of the keyboard can be anything and doesn't need to be `my_keyboard`.
- In the run phase: Collect a keyboard with `key, t = my_keyboard.get_key(keylist=['q', 'p'], timeout=2000)`
- The `keylist` and `timeout` parameters can also be passed during initialization: `my_keyboard = Keyboard(keylist=['q', 'p'], timeout=2000)`

The answer should not not:

- Refer to a `keyboard_response` item
- Use JavaScript
- Initialize the keyboard with a lowercase function
- Pass `exp` as argument when initializing the keyboard
