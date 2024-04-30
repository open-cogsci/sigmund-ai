In a loop item I have a trial sequence. In every trial I want to show a trial-specific image. How should I define or name these images in the loop item and how can I make sure that for each trial, the correct image is shown? I already have the images in my file pool and I want to use only the GUI.

The answer should: 

-	Suggest adding a new column (or variable) to the loop table in the loop item and name it `image_file`. The name of the column (or variable) can be anything and doesn’t need to be `image_file`.
-	In each row of the column, reference the filename of the image you want to display for that trial (e.g., image1.jpg, image2.jpg, etc.). 
-	In the sequence that the loop is calling, add a sketchpad item for displaying the image.
-	To make sure the sketchpad displays the correct image for each trial the answer should mention either one of the following two options: 1: directly modify the sketchpad script by adding the following line: `draw image 0 0 {image_file}`. Or 2: In the sketchpad item, click on the image tool (icon with a mountain landscape) and then click where you want your image to appear on the screen, first choose any image. After you added the image, double click on it and in the element script window that pops up, change the file name to `{image_file}`. 

The answer should *not*:

-	Refer to python inline_scritp
-	Refer to java_inline script
-	When adding an image element, directly type the name of the loop column into the file name field of the image tool dialog.
-   Put square brackets around the column name when adjusting the sketchpad or element script, for example: `[image_file]`.
