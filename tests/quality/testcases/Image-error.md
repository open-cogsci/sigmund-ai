I have an experiment where I want to present an image to a participant for 10 seconds. I used the code below to upload the image:  
canvas \= Canvas()  
canvas.image("stimulus.png", x=0, y=0)   
canvas.show()  
clock.sleep(10000)    
However, when I run the experiment, I keep getting the error: FileNotFoundError: \[Errno 2\] No such file or directory: 'stimulus.png'  
How can I fix it?

The answer should:

- Inform the user that the image file is not in the file pool of the experiment  
- Provide the solution to the problem, either by adding the file to the pool or by adding a pool reference in the code 

