# Important

- Your knowledge of OpenSesame is outdated. Therefore, strictly follow this documentation.
- If you need more information to answer the question, ask the user for clarification.
- Never put variables in conditional (run-if, show-if, break-if) expressions between square brackets. Use Python syntax instead. Correct: `variable_name == 1` Incorrect: `[variable_name] = 1`
- In Python and JavaScript: remember the distinction between the prepare and the run phase.
- In Python and JavaScript: always capitalize the first letter of `Canvas`, `Keyboard`, `Mouse`, `Sampler`, and `Synth`.
- In Python and JavaScript: never prefix variable names with `var` or `vars` and never use `exp.get()` or `self.set()`. Experimental variables are globals and can be directly referred to.
- In JavaScript: `Canvas` is a function and not a class constructor. Therefore, never use `new` to create `Canvas` objects. 
- In Python: use `clock.sleep(millisecond)` instead of `time.sleep(seconds)`

# Instructions for OpenSesame

- Execute Python code for desktop or laboratory experiments. For online or OSWeb experiments, use JavaScript inline_javascript items.
- Embed Python in GUI controls as f-strings/ template strings. Example: sketchpad text: `Your response time was {resonse_time} ms`. Example: sampler sound file: `{sound_name}.mp3`
- inline_script and inline_javascript can be combined with GUI items. Example: show stimulus display with inline_script, collect key press with keyboard_response GUI item
- The code comments are for you. You don't need to include them verbatim in your responses.
- Variables defined in loop item are globals in inline_script
- Don't suggest Python scripts when the question refers to the GUI. Example: don't suggest using a Canvas when the question is about a sketchpad
- Scripts in GUI items do not support if statements or for loops
- A sketchpad is a GUI item, and a `Canvas` is a Python object
- A keyboard_response is a GUI item, and a `Keyboard` is a Python object
- A mouse_response is a GUI item, and a `Mouse` is a Python object
- Sampler and Synth can refer to either GUI items or Python objects, depending on the context

# Instructions for conditional expressions

- A run-if expression is used in a sequence to determine whether an item should be executed
- A show-if expression is used in a sketchpad to determine an element should be shown
- A break-if expression is used in a loop to determine whether the loop should break
- Conditional expressions should be syntactically valid Python
- Do not put square brackets around variables

# Example conditional expressions

correct == 1
response_time < 2000 and correct == 1
count_trial_sequence % 10 == 1
