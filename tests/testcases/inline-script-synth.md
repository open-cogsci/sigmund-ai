I would like to play a beep with a frequency of 440 Hz using a Python script. Can you show me how?

The answer should:

- Refer to a Python inline_script
- Indicate that the synth should be prepared in the prepare phase and played in the run phase
- In the prepare phase: Initialize a synth as follows: `my_synth = Synth(freq=440, length=1000)`. The name of the synth can be anything and doesn't need to be `my_synth`. The duration can also be anything and doesn't need to be 1000.
- In the run phase: play the sound: `my_synth.play()`

The answer should not not:

- Refer to a synth item in the GUI
- Use JavaScript
- Pass `exp` as argument when initializing the synth, although other arguments may be passed as explained above
