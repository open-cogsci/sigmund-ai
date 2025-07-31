How do I make an experiment where the participant has to name objects that appear on the screen?

The answer should:

- Guide the user how to create the experiment with the following steps::  
* Open OpenSesame and create a new experiment.  
* Choose a "Legacy" or "PsychoPy" backend for better response recording.  
* Set the resolution and refresh rate.   
* IIn the sequence tab, include:  
* practice\_loop (optional)  
* experiment\_loop  
* fixation\_cross  
* stimulus\_display  
* voice\_response  
* logger  
* Add a loop item (experiment\_loop) that contains a table.  
* Include a column for object names and image file names and set the repeat value (e.g., if you want each item to appear once).  
* Inside experiment\_loop, add a sketchpad item (stimulus\_display).  
* Click "Image" and insert "\[image\]" (this dynamically loads images).  
* Set duration to 0 (so it moves to the next step immediately).  
* Add a "keyboard\_response" or "voice\_response" item after stimulus\_display.  
* For voice responses:  
  * Use the voice\_response plugin (ensure microphone access).  
  * Set "Duration" to 3000 ms (3 sec for response).  
  * Enable "Save sound?" to record audio.  
  * Define filename format: response\_\[subject\_nr\]\_\[count\].wav.  
* Before each trial, add a sketchpad (fixation\_cross) with a centered "+".  
* Duration: 500 ms.  
* Add a logger at the end of the loop to save:  
  * image (stimulus presented)  
  * object\_name (expected answer)  
  * response\_time  
  * voice\_response (filename of recorded audio)  
* Run the experiment and check the log file (.csv) to see if responses are stored correctly.

