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
