How can I design an experiment where a person is presented with a series of true/false statements with a keyboard response? I want the allowed responses to be T for true and F for false

The answer should:

- Provide a step-by-step guide for implementing a True/False task and emphasise the GUI method  
- Mention other possible design methods, such as using an inline script.  
- Specify the design steps:   
  - Add a sequence  
  - Add a loop and append to it:  
    - Sequence  
    - Sketchpad  
    - Keyboard response  
    - Logger  
  - Then, go to the loop item and add a column “statement”  with the statements, 1	 statement per row  
  - In the Sketchpad and add text \[statement\]  
  - For Keyboard Response set Allowed Keys to T and F and choose Store Response Time  
  - In the logger, ensure that it contains: statement, response and response\_time  
  - Run the experiment  
- Specify how to configure following elements: Loop, Sketchpad, Keyboard Response, Logger

The answer should not:

- Describe alternative design methods in detail  
- Assume which method is used and provide only one possible answer