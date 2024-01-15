I have a file called `beep.mp3` in the file pool. I would like to play this file using a Python script. Can you show me how?

The answer should:

- Refer to a Python inline_script
- Indicate that the sampler should be prepared in the prepare phase and played in the run phase
- In the prepare phase: Initialize a sampler as follows and pass the sound file as an argument: `my_sampler = Sampler(sound_file)`. The name of the sampler and the sound file can be anything and don't need to be `my_sampler` and `sound_file`.
- In the run phase: play the sound: `my_sampler.play()`

The answer should not not:

- Refer to a sampler item in the GUI
- Use JavaScript
- Pass `exp` as argument when initializing the sampler, although other arguments may be passed as explained above
