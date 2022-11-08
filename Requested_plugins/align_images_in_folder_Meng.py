#@ File (label = "Input directory", style = "directory") srcFile
#@ File (label = "Reference image", style = "file") reference
#@ String  (label = "File extension", value=".tif") ext
#@ String  (label = "File name contains", value = "") containString
#@ Integer (label = "Nucleus channel", min=1, value=1) ref_ch

from ij import IJ, WindowManager
import os
from ij.plugin import ZProjector, Duplicator


def run():
	srcDir = srcFile.getAbsolutePath()
	dstDir = srcDir + "_results"
	reference_path = reference.getAbsolutePath()
	
	if not os.path.exists(dstDir):
		os.mkdir(dstDir)	
	
	print("Input folder: " + srcDir)
	print("reference file: " + reference_path)
	ref = IJ.openImage(reference_path)
	ref.show()
	for root, directories, filenames in os.walk(srcDir):
		filenames.sort();
		for filename in filenames:
			# Check for file extension
			if not filename.endswith(ext):
				continue
			# Check for file name pattern
			if containString not in filename:
				continue
			if os.path.basename(str(reference)) in filename:
				continue
			process(ref, filename, srcDir, dstDir)

def process(ref, target_path, currentDir, outputDir):
	print("Processing: " + target_path)	
	target = IJ.openImage(os.path.join(currentDir, target_path))
	
	nuc = Duplicator().run(target, ref_ch, ref_ch, 1, 1, 1, 1)
	
	IJ.run(nuc, "Rigid Registration", "initialtransform=[] n=1 tolerance=1.000 level=6 stoplevel=2 materialcenterandbbox=[] showtransformed template=" + os.path.basename(str(target_path)) + " measure=Euclidean");
	
	WindowManager.getImage("transformed")
	transformed_target = IJ.getImage()
	
	
	ref.hide()
	target.close()
	
	# save
	transformed_target.save(os.path.join(outputDir, os.path.splitext(target_path)[0]))
	
	transformed_target.close()
	
	
IJ.run("Close All", "")
run()



#reference = IJ.openImage("C:/Users/oodegard/Desktop/unaligned micropatterning fixed images/C20220319_1500CB_2xFyVE_012.tif");
#print(reference.getName())

#target = IJ.openImage("C:/Users/oodegard/Desktop/unaligned micropatterning fixed images/B20220319_1500CB_005.tif");

#IJ.run(reference, "Rigid Registration", "initialtransform=[] n=1 tolerance=1.000 level=6 stoplevel=2 materialcenterandbbox=[] showtransformed template=" + + " measure=Euclidean");