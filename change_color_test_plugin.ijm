/*
 * This is a test script that changes the color of your image according to the lookup table that you define
 * There can be more colors in your list than you have channels, but if you have too few the script will not change the "missing channels"
 * Please fell free to change or optimize this script
 * It will open a sample image if none are open
 */
 
#@ String (visibility=MESSAGE, value="This is a script that changes the look up table (LUT) of your image (Currently selected).", required=false) msg
#@ String (visibility=MESSAGE, value="You can choose all colors that are allowed in ImageJ.", required=false) msg2
#@ String (label = "Select colors (comma separated) E.g 'Cyan,Magenta,Green'", value = "Cyan,Magenta,ffre") csvcol

// See also Process_Folder.py for a version of this code
// in the Python scripting language.


// Check that there is an image open
if(nImages==0){
	showMessage("No image was open. A sample image will be used");
	run("Fluorescent Cells");
	//exit("No images are open");
}

// Check that there are colors in iput
colors = split(csvcol, ",");
if (lengthOf(colors)==0) {
	exit("No colors selected");
}

// Run
// Stack.setDisplayMode("color");
Stack.setDisplayMode("composite");


getDimensions(width, height, channels, slices, frames);
for (i = 1; i <= channels; i++) {
	Stack.setChannel(i);
	run(colors[i-1]); 
}



