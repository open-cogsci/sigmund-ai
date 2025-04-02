How do I make an experiment with a series of True/False statements? I want to record when a participant presses the keys T for “True” and F for “False”. 

The answer should:

**Option 1:** Guide the user how to create the experiment in Open Sesame, but inform that there are other methods possible to design it. The answer should include that the experiment needs to have the keyboard press GUI, where it can be selected which keys the experimenter wants to have recorded.   
**Option 2:** Provide all possible options; guide the user how to create the experiment with them. Inform where the data will be stored after the experiment is done.

Step-by-step guide  
How to do an experiment in OpenSesame:  
Open OpenSesame & create a new experiment  
Add a loop and append to it:  
Sketchpad  
Keyboard response  
Logger  
Then, go to the loop item and add a column “statement”  with the statements, 1	 statement per row  
In the Sketchpad, add text \[statement\]  
For Keyboard Response set Allowed Keys to T and F and choose Store Response Time  
In the logger, ensure that it contains: statement, response and response\_time  
Run the experiment  
Navigate where to find the data → For OpenSesame  
**Shouldn’t** assume which method is used and provide only one possible answer

* **Score**: 3, doesn’t provide alternative options  
  * Possible Solution: Specify that the experiment is done in OpenSesame or remove that requirement, have it just to mention that it depends where the experiment is done, but in OpenSesame this is how it looks like:...