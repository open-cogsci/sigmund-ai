# Run-if expression (GUI)

I have a sketchpad that I would like to show only after an incorrect response. Can you show me how to do that?'

The answer should:
        
- Mention the run-if expression: `correct == 0`
- Explain that this run-if expression should be used in a sequence item

The answer should *not*:

- Refer to Python inline_script or contain other Python code
- Refer to JavaScript inline_javascript or contain other JavaScript code
- Refer to a show-if expression


# Show-if expression (GUI)

I have a single sketchpad that contains a central arrow cue. I have defined a `cue` variable in a loop, which can be "right" or "left". Depending on this variable I would like to show either a leftwards or rightwards arrow. Can you show me how?

The answer should:

- Mention show-if expressions: `cue == "left"` and `cue == "right"`
- Explain that these show-if expressions should be assigned to two different arrow elements in the sketchpad

The answer should * not*:

- Refer to Python inline_script or contain other Python code
- Refer to JavaScript inline_javascript or contain other JavaScript code
- Refer to a run-if expression or use multiple sketchpads


# Canvas FixDot (Python)

I would like to use a Python inline script to show a stimulus display containing a central fixation dot. Can you show me how?

The answer should:

- Refer to a Python inline_script
- Indicate that the canvas should be prepared in the prepare phase and shown in the run phase
- In the prepare phase: Initialize a canvas with an uppercase function without any arguments: `my_canvas = Canvas()`. The name of the canvas can be anything and doesn't need to be `my_canvas`.
- In the prepare phase: Add a fixation dot to the canvas using `my_canvas.fixdot()`, `my_canvas += FixDot()`, or `my_canvas['fixdot'] = FixDot()`. If a name is used for the FixDot element, this name can be anything and doesn't need to be 'fixdot'.
- In the run phase: Show the canvas with `my_canvas.show()`

The answer should not not:

- Refer to a `sketchpad` or `feedback` item
- Use JavaScript
- Initialize the canvas with a lowercase function
- Pass any arguments when initializing the canvas 


# Canvas FixDot (JavaScript)

I would like to use a script to show a stimulus display containing a central fixation dot in OSWeb. Can you show me how?

The answer should:

- Refer to a JavaScript inline_javascript
- Indicate that the canvas should be prepared in the prepare phase and shown in the run phase
- In the prepare phase: Initialize a canvas with an uppercase function without any arguments: `var my_canvas = Canvas()`. The name of the canvas can be anything and doesn't need to be `my_canvas`.
- In the prepare phase: Add a fixation dot to the canvas using `my_canvas.fixdot()`
- In the run phase: Show the canvas with `my_canvas.show()`

The answer should not not:

- Refer to a `sketchpad` or `feedback` item
- Use Python
- Use the `new` keyword to initialize the canvas
- Pass any arguments when initializing the canvas


# Keyboard (Python)

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


# Mouse (Python)

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


# Sampler (Python)

I have a file called `beep.mp3` in the file pool. I would like to play this file using a Python script. Can you show me how?

The answer should:

- Refer to a Python inline_script
- Indicate that the sampler should be prepared in the prepare phase and played in the run phase
- In the prepare phase: Initialize a sampler with an uppercase function: `my_sampler = Sampler()`. The name of the keyboard can be anything and doesn't need to be `my_sampler`.
- In the run phase: play the sound: `my_sampler.play()`

The answer should not not:

- Refer to a sampler item in the GUI
- Use JavaScript
- Initialize the sampler with a lowercase function
- Pass `exp` as argument when initializing the sampler


# Synth (Python)

I would like to play a beep with a frequency of 440 Hz using a Python script. Can you show me how?

The answer should:

- Refer to a Python inline_script
- Indicate that the synth should be prepared in the prepare phase and played in the run phase
- In the prepare phase: Initialize a synth with an uppercase function: `my_synth = Synth()`. The name of the keyboard can be anything and doesn't need to be `my_synth`.
- In the run phase: play the sound: `my_synth.play()`

The answer should not not:

- Refer to a synth item in the GUI
- Use JavaScript
- Initialize the synth with a lowercase function
- Pass `exp` as argument when initializing the synth


# Clock (Python)

I would like to insert a delay of 1.5 s using a Python script. How can I do that?

The answer should:

- Refer to a Python inline_script
- Use `clock.sleep(1500)`

The answer should not not:

- Refer to durations specified in GUI items
- Use JavaScript
- Use `self.sleep()`
- Use the Python `time` module


# Logger (GUI)

My OpenSesame log file contains many variables that I don't need. I would like to select only a handful of relevant variables, such as condition, response time, correct, subject_nr, etc. How can I do that?

The answer should:

- Refer to the logger GUI item
- Suggest disabling the 'Automatically log all variables' option
- Suggest adding variables to the 'Include' list

The answer should *not*:

- Refer to the Python `log` object
- Refer to Python inline_script or contain other Python code
- Refer to JavaScript inline_javascript or contain other JavaScript code


# Enabling OSWeb (GUI)

I would like to run my experiment in a browser, but it always opens in a separate window when I run it. How can I run my experiment in a browser?

The answer should:

- Suggest selecting 'In a browser with OSWeb' in experiment properties
- Indicate that not all functionality is available when running in a browser


# Publishing to JATOS (GUI)

How can I create a link so that participants can run my experiment online?

The answer should:

- Indicate that the experiment should be set to run 'In a browser with OSWeb' in experiment properties
- Indicate that you need to upload the experiment to a JATOS server
- Option 1:
    - Indicate that once you're logged into JATOS, you can generate an API token, which should be entered in OpenSesame in the OSWeb and JATOS control panel
    - Indicate that you can now use the 'Publish to JATOS' option in OpenSesame
- Option 2:
    - Indicate that you can export the experiment in OpenSesame and import it in the JATOS web interface
- Option 1 and option 2 are both ok, but option 1 is preferred
