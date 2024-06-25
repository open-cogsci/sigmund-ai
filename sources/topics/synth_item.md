# synth item

The synth item generates simple sounds.

Options:

- Waveform: sine, saw, square, or white_noise
- Frequency: in Hertz
- Attack: fade-in value in milliseconds
- Decay: fade-out value in milliseconds
- Volume: a numeric value where 0 is silence and 1 is maximum volume
- Panning: a numeric value where negative is panning left and positive is panning right; 'left' for full-left panning; 'right' for full-right panning.
- Length: the length of the generated sound.
- Duration: a numeric duration in milliseconds (after which the experiment continues while the sound continues to play if the length is longer than the duration), 'sound' (to wait until the sound is finished playing), 'keypress' (to wait until a key is pressed) or 'mouseclick' (to wait until a mouse button is clicked).

More information:

- <https://osdoc.cogsci.nl/4.0/manual/stimuli/sound/>
