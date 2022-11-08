#@ File    (label = "Input directory", style = "directory") srcFile
## File    (label = "Output directory", style = "directory") dstFile
#@ String  (label = "File extension", value=".tif") ext
#@ String  (label = "File name contains", value = "") containString
#@ Integer (label = "Nucleus channel", min=1, value=1) nuc_ch
#@ boolean (label = "Manual check on nuclear segmentation", value = true) check_nuc_roi

# See also Process_Folder.ijm for a version of this code
# in the ImageJ 1.x macro language.

import os
from ij import IJ, ImagePlus, WindowManager
from ij.plugin import ZProjector, Duplicator
from ij.plugin.frame import RoiManager
from loci.plugins import BF
from ij.gui import OvalRoi, Roi, WaitForUserDialog, PointRoi
from ij.text import TextWindow
from ij.measure import ResultsTable
import glob

def run():
	srcDir = srcFile.getAbsolutePath()
	#dstDir = dstFile.getAbsolutePath()
	dstDir = srcDir + "_" + output_folder_name

	if srcDir == dstDir:
		sys.exit("srcDir == dstDir is not allowed")
	if not os.path.exists(dstDir):
		os.mkdir(dstDir)		
	
	for root, directories, filenames in os.walk(srcDir):
		filenames.sort();
		for filename in filenames:
			# Check for file extension
			if not filename.endswith(ext):
				continue
			# Check for file name pattern
			if containString not in filename:
				continue
			process(srcDir, dstDir, root, filename)
	rt = makeResultsTable(dstDir, nuc_seg_ext, nucleus_annotation_ext)
	rt.save(os.path.join(dstDir, "Results.tsv"))
 
def process(srcDir, dstDir, currentDir, fileName):
	print "Processing:"
	# Opening the image
	print "Open image file", fileName
	imps = BF.openImagePlus(os.path.join(currentDir, fileName))
	
	# Make a output file name base to use for saving
	outNameBase = os.path.splitext(os.path.basename(str(fileName)))[0]
	
	# Make empty closed ROI managers
	rm_nuc_rois = RoiManager(False)
	rm_annotations = RoiManager(False)
	
	for imp in imps:
		# Max project if  number of z dimension > 1
		if(imp.getDimensions()[3]>1):
  			imp = ZProjector.run(imp,"max all")
		
		nuc_roi_zip_name = os.path.join(dstDir, outNameBase + "_"  + nuc_seg_ext )
		
		# Locate nuclei in each image
		if(os.path.exists(nuc_roi_zip_name + ".zip")):
			rm_nuc_rois.open(nuc_roi_zip_name + ".zip")
		elif(os.path.exists(nuc_roi_zip_name + ".roi")):
			rm_nuc_rois.open(nuc_roi_zip_name + ".roi")
		
		rm_nuc_rois = findNucleus(imp, nuc_ch, rm_nuc_rois)
		
		## Save
		if(rm_nuc_rois.getCount() == 0):
			IJ.saveString("No ROIs", nuc_roi_zip_name + ".txt")
		elif(rm_nuc_rois.getCount() == 1):
			rm_nuc_rois.save(nuc_roi_zip_name + ".roi")
		elif(rm_nuc_rois.getCount() > 1):
			rm_nuc_rois.save(nuc_roi_zip_name + ".zip")		
			
		
		# Annotate cells
		for i, r in enumerate(rm_nuc_rois.getRoisAsArray()):
			annotation_roi_zip_name = os.path.join(dstDir, outNameBase + "_" + nucleus_annotation_ext + "_" + str(i))
			
			if(os.path.exists(annotation_roi_zip_name + ".zip")):
				rm_annotations.reset()
				rm_annotations.open(annotation_roi_zip_name + ".zip")
			elif(os.path.exists(annotation_roi_zip_name + ".roi")):
				rm_annotations.reset()
				rm_annotations.open(annotation_roi_zip_name + ".roi")
			
			rm_annotations = annotate_roi(imp, r, rm_annotations)
			
			## Save
			if(rm_annotations.getCount() == 0):
				IJ.saveString("No ROIs", annotation_roi_zip_name + ".txt")
			elif(rm_annotations.getCount() == 1):
				rm_annotations.save(annotation_roi_zip_name + ".roi")
			else:
				rm_annotations.save(annotation_roi_zip_name + ".zip")
				
			
			rm_annotations.reset()
			
		imp.close()

def findNucleus(imp, nuc_ch, rm_nuc_rois):
	
	
	IJ.setForegroundColor(255, 255, 255);	
	
	# This must be a single slice image
	nuc = Duplicator().run(imp, nuc_ch, nuc_ch, 1, 1, 1, 1)
	IJ.run(nuc, "Gaussian Blur...", "sigma=" + str(nucBlurSigma));
	
	IJ.setAutoThreshold(nuc, "MaxEntropy dark");
	IJ.run(nuc, "Convert to Mask", "MaxEntropy dark")
	IJ.run(nuc, "Fill Holes", "");

	if(rm_nuc_rois.getCount() == 0):
		# Find particles
		# Do not show this ROI manager	
		# nuc.show()
		IJ.run(nuc, "Create Selection", "");
		
		
		#IJ.setThreshold(nuc, 255, 255)
		IJ.run(nuc, "Analyze Particles...", "size=" + str(minNucSize) + "-Infinity pixel exclude clear overlay");
		
		
		composite_rois = nuc.getRoi()
				
		# make polygon rois iteratable
		# ShapeRoi works out of the box
		
		
		if(composite_rois.getClass().__name__ == "PolygonRoi"):
			rm_nuc_rois_array = [composite_rois]
		else:
			rm_nuc_rois_array = composite_rois.getRois()
		
		for r in rm_nuc_rois_array:
			rm_nuc_rois.addRoi(r)
		
	if(check_nuc_roi):
		rm_display = displayRois(rm_nuc_rois)
		nuc2 = Duplicator().run(imp, nuc_ch, nuc_ch, 1, 1, 1, 1)
		nuc2.show()
		myWait = WaitForUserDialog("Evaluate", "Edit segmentation in Roi Manager")
		myWait.show()
		rm_nuc_rois.reset()
		
		for r in rm_display.getRoisAsArray():
			rm_nuc_rois.addRoi(r)

		rm_display.reset()
		rm_display.close()
		
		if(WindowManager.getImageCount() == 0):
			rm_display.close()
			sys.exit()
		else:
			nuc2.changes = False
			nuc2.close()
	
	# displayRois(rm_nuc_rois)
	return(rm_nuc_rois)

def annotate_roi(imp, single_roi, rm_annotations):
	# Make composite image to show
	imp.setDisplayMode(IJ.COMPOSITE);
	imp.show()
	imp.hide()			
	imp_flat = imp.flatten()
	imp_flat.show()
	
	# Add roi as selection to image
	imp_flat.setRoi(single_roi)
	IJ.run("Line Width...", "line=" + str(nuc_linewidt));
	IJ.setForegroundColor(255, 255, 0);
	IJ.run(imp_flat, "Draw", "slice");
	
	
	# ROI manager setup
	
	rm_display = displayRois(rm_annotations)

	IJ.setTool("point")
	IJ.run("Point Tool...", "type=Hybrid color=Yellow size=[Extra Large] auto-next add")
	
	rm_display.runCommand("Associate", "true")
	rm_display.runCommand("Centered", "false")
	rm_display.runCommand("UseNames", "false")

	# Open image and show OKbutton
	rm_display.runCommand(imp_flat,"Show All");
	myWait = WaitForUserDialog("Select ROIs", "Select one or more ROIs covering each feature to track")
	myWait.show()
		
	# Exit program if image is closed
	if(WindowManager.getImageCount() == 0):
		rm_display.close()
		sys.exit()
	else:
		
		# Copy ROis from manager to rm_annotation
		rm_annotations.reset()
		for i, r in enumerate(rm_display.getRoisAsArray()):
			rm_annotations.addRoi(r)
		
		# Close		
		imp_flat.changes = False
		imp_flat.close()
		rm_display.reset()
		rm_display.close()
	
	# return ROI Manager
	return rm_annotations

def makeResultsTable(dstDir, nuc_seg_ext, nucleus_annotation_ext):
	nuc_annotation = glob.glob(dstDir + '/*_nuc_seg*')

	# Make results table
	rt_exist = WindowManager.getWindow("Results table")
	if rt_exist==None or not isinstance(rt_exist, TextWindow):
	    rt= ResultsTable()
	else:
	    rt = rt_exist.getTextPanel().getOrCreateResultsTable()
	    rt.reset()
	rt_counter = 0
	
	image_id = 0
	
	for p in nuc_annotation:
		if(p.endswith(".zip") or p.endswith(".roi")):
			# Nucleus segmentation
			rm_nuc_rois = RoiManager(False)
			rm_nuc_rois.open(p)
			nNuc = rm_nuc_rois.getCount()
			print("Number of nuclei: " + str(nNuc))
			
			# Annotation
			basename = os.path.splitext(os.path.basename(str(p)))[0].replace("_" + nuc_seg_ext, "")
			annotation_paths = glob.glob(dstDir + "/" + basename + "_" + nucleus_annotation_ext + "*")
			annotation_id = 0
			for ap in annotation_paths:	
				rm_annotations = RoiManager(False)
				
				if(ap.endswith(".zip")):
					rm_annotations.open(ap)
					nAnnotations = rm_annotations.getCount()
				elif(ap.endswith(".roi")):
					#rm_annotations.open(ap)
					#nAnnotations = rm_annotations.getCount()
					nAnnotations = 1
				else:
					nAnnotations = 0 
				print("Number og annotations: " + str(nAnnotations))
				
				# Add to results table
				rt.setValue("path", rt_counter, ap);
				rt.setValue("image_ID", rt_counter, image_id);
				rt.setValue("annotation_ID", rt_counter, annotation_id);
				
				rt.setValue("nAnnotations", rt_counter, nAnnotations);
							
					
				rt_counter = rt_counter + 1
				annotation_id = annotation_id + 1
		image_id = image_id + 1
	rt.show("Results table")
	return(rt)
	

def displayRois(rm):
	# Function that open a display Roi Manager and adds a hidden roi manager object to it
	# rm needs to have been started with RoiManager(False) call

	# Make visible Roi Manager
	rm_display = RoiManager.getRoiManager()
	rm_display.show()
	rm_display.reset()
	
	for r in rm.getRoisAsArray():
		rm_display.addRoi(r)
	return(rm_display)


# Input
minNucSize = 100
nuc_linewidt = 5
nuc_seg_ext = "nuc_seg"
nucleus_annotation_ext = "point_annotation"
output_folder_name = "annotation"

nucBlurSigma = 5


# Run
rm = RoiManager.getInstance()
if(rm!= None):
	rm.close()
IJ.run("Close All", "")	
run()
