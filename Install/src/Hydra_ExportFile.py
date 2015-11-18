# Hydra: A Plugin for example file sharing
# 
# This file is part of Hydra.


"""
Use this component to export your GH file to your Hydra repository so that you can upload and share with the community!
-
Provided by Hydra 0.0.02

    Args:
        _fileName: A text name for your example file.
        _fileDescription: A text description of your example file.  This can be a list and each item will be written as a new paragraph.
        changeLog_: A text description of the changes that you have made to the file if this is a new version of an old example file.
        fileTags_: An optional list of test tags to decribe your example file.  This will help others search for your file easily.
        targetFolder_: Input a file path here to the hydra folder on you machine if you are not using the default Github structure that places your hydra github repo in your documents folder.
        includeRhino_: Set to 'True' to include the Rhino file in the zip file that gets uploaded to your hydra fork.  This is important if you are referencing Rhino geometry and have not internalized it in the GH document.  By default, this is set to 'False', which will only include the grasshopper file.
        GHForThumb_: Set to 'True' to have the thumbnail of your example file be of your GH canvas.  By default, the thumbnail will be of the Rhino scene since this is where the cool geometric output of the file displays.  If your file is not producing a geometric output, you will want to set this to 'True.'
        additionalImgs_: A list of file paths to additional images that you want to be shown in Hydra page 
        _export: Set to "True" to export the Grasshopper file to Hydra.
    Returns:
        readMe!: ...
"""

ghenv.Component.Name = "Hydra_ExportFile"
ghenv.Component.NickName = 'exportHydra'
ghenv.Component.Message = 'VER 0.0.02\nNOV_18_2015'
ghenv.Component.Category = "Extra"
ghenv.Component.SubCategory = "Hydra"
try: ghenv.Component.AdditionalHelpFromDocStrings = "1"
except: pass

import Grasshopper.Kernel as gh
import scriptcontext as sc
import shutil
import os
import zipfile
import Grasshopper.GUI as ghGUI
import System
import Grasshopper.Instances as ghInst
import time
from time import mktime
from datetime import datetime
import json
import Rhino as rc


def checkTheInputs():
    # Set a warning variable.
    w = gh.GH_RuntimeMessageLevel.Warning
    c = gh.GH_RuntimeMessageLevel.Remark
    
    #Replace any spaces in the connected fileName with underscores.
    fileName = _fileName.strip().replace(" ","_")
    
    #Set a default directory to the Github default if none has been input.
    checkData1 = True
    repoTargetFolder = None
    fullForkTarget = None
    if targetFolder_:
        if not os.path.isdir(targetFolder_):
            checkData1 = False
            warning = "The connected directory to targetFolder_ does not exist on your machine."
            print warning
            ghenv.Component.AddRuntimeMessage(w, warning)
        else:
            if targetFolder_.endswith('\\'):
                repoTargetFolder = targetFolder_ + fileName
                fullForkTarget = targetFolder_
            else:
                repoTargetFolder = targetFolder_ + '\\' + fileName
                fullForkTarget = targetFolder_ + '\\'
    else:
        hydraFolder = None
        username = os.getenv("USERNAME")
        githubDirectory = "C:\\Users\\" + username + "\\Documents\\GitHub\\"
        for file in os.listdir(githubDirectory):
            if 'hydra' in file: hydraFolder = githubDirectory + file + "\\"
        if hydraFolder == None: hydraFolder = "C:\\Users\\" + username + "\\Documents\\GitHub\\hydra\\"
        if not os.path.isdir(hydraFolder):
            checkData1 = False
            warning = "The component cannot automatically find the hydra repo on your machine. \n Plug in the correct file path of the hydra repo to the targetFolder_ input on this component."
            print warning
            ghenv.Component.AddRuntimeMessage(w, warning)
        else:
            repoTargetFolder = hydraFolder + fileName
            fullForkTarget = hydraFolder
    
    
    # Check the directory and create it if it does not exist.  If it does exist, it is, there is not an old version of this example file and I should make a new directory.
    gitUserTrigger = False
    gitUserName = None
    forkName = None
    checkData2 = True
    if repoTargetFolder != None:
        
        #Pull out the username from the config file.
        configFile = fullForkTarget + '.git\\config'
        if os.path.isfile(configFile):
            with open(configFile, "r") as cnfFile:
                for lineCount, line in enumerate(cnfFile):
                    if '[remote "origin"]' in line: gitUserTrigger = True
                    elif gitUserTrigger == True and 'https://github.com/' in line:
                        gitUserName = line.split('https://github.com/')[-1].split('/')[0]
                        forkName = line.split('/')[-1].split('.git')[0]
                        gitUserTrigger = False
        else:
            checkData2 = False
            warning = "Could not find the config file in your Hydra fork on your system. \n Make sure that you have cloned hydra to your system. \n If you have cloned hydra, plug in the correct file path of the hydra repo to the targetFolder_ input on this component."
            print warning
            ghenv.Component.AddRuntimeMessage(w, warning)
    
    #Make a list of file tags that includes the example file name if nothing else is connected.
    if len(fileTags_) == 0:
        fileTags = []
        for word in _fileName.split(' '):
            fileTags.append(word)
    elif len(fileTags_) == 1 and ',' in fileTags_[0]:
        fileTags = fileTags_[0].split(',')
    elif len(fileTags_) == 1 and ';' in fileTags_[0]:
        fileTags = fileTags_[0].split(';')
    elif len(fileTags_) == 1:
        fileTags = fileTags_[0].split('\n')
    else:
        fileTags = fileTags_
    
    if not 'Grasshopper' in fileTags and \
       not 'grasshopper' in fileTags:
        fileTags.append('Grasshopper')
    
    fileTags = [tag.strip() for tag in fileTags]
    
    #Check to be sure that the user has saved this currently open GH file so that we can copy it.
    checkData3 = True
    document = ghenv.Component.OnPingDocument()
    doucumentPath = document.FilePath
    if doucumentPath!=None and os.path.isfile(doucumentPath): pass
    else:
        checkData3 = False
        warning = "You have not yet saved this Grasshopper file to your machine. \n You must save it first in order to export it to Hydra."
        print warning
        ghenv.Component.AddRuntimeMessage(w, warning)
    
    #Check to be sure that the user has saved this currently open Rhino file so that we can copy it.
    checkData4 = True
    rhinoDocPath = rc.RhinoDoc.ActiveDoc.Path
    if os.path.isfile(rhinoDocPath): pass
    elif not os.path.isfile(rhinoDocPath) and includeRhino_ == True:
        checkData4 = False
        warning = "You must save your Rhino file in order to export it to Hydra. \nEither save your file or set 'includeRhino_' to 'False'."
        print warning
        ghenv.Component.AddRuntimeMessage(w, warning)
    else:
        comment = "You have not yet saved this Rhino file to your machine. \nYou will be able to use the 'includeRhino_' input to this component to include the rhino file with your example."
        print comment
        ghenv.Component.AddRuntimeMessage(c, comment)
    
    #Give a final check for everything.
    if checkData1 == True and checkData2 == True and checkData3 == True and checkData4 == True: checkData = True
    else: checkData = False
    
    
    return checkData, fileName, _fileDescription, fileTags, repoTargetFolder, doucumentPath, document, rhinoDocPath, gitUserName, forkName


def writeGHRhino(fileName, repoTargetFolder, doucumentPath, rhinoDocPath):
    #Write out a list for the source files.
    zipFileDirectory = repoTargetFolder + '\\' + fileName
    if not os.path.isdir(zipFileDirectory): os.mkdir(zipFileDirectory)
    
    #Write out a GH file to the folder.
    ghFilePath = zipFileDirectory + '\\' + fileName + '.gh'
    shutil.copyfile(doucumentPath, ghFilePath)
    
    #If the user has requested writing the Rhino file, write it there.
    rhinoWritten = False
    rhioDestinationPath = zipFileDirectory + '\\' + fileName + '.3dm'
    if includeRhino_:
        if rhinoDocPath != '':
            shutil.copyfile(rhinoDocPath, rhioDestinationPath)
            rhinoWritten = True
    else:
        rhioDestinationPath = zipFileDirectory + '\\' + fileName + '.3dm'
        if os.path.isfile(rhioDestinationPath):
            os.remove(rhioDestinationPath)
    
    #Zip the files together.
    zipFilePath = repoTargetFolder + '\\' + fileName
    
    zf = zipfile.ZipFile("%s.zip" % (zipFilePath), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(zipFileDirectory)
    for dirname, subdirs, files in os.walk(zipFileDirectory):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            zf.write(absname, arcname)
    zf.close()
    
    #Delete the old zip directory.
    shutil.rmtree(zipFileDirectory)
    
    return zipFilePath


def writeReadMe(fileName, fileDescription, repoTargetFolder, changeLog, gitUserName, fileTags, forkName):
    readMeFilePath = repoTargetFolder + '\\' + 'README.md'
    
    #Write the description.
    readMeFile = open(readMeFilePath, "w")
    readMeFile.write('### Description \n')
    for line in fileDescription:
        readMeFile.write(line + '\n')
    readMeFile.write('\n')
    
    #Write in a link to the user's page and to the hydra page.
    readMeFile.write('This file has been submitted by [' + gitUserName + '](https://github.com/' + gitUserName + ')')
    readMeFile.write('\n')
    readMeFile.write('\n')
    readMeFile.write('[Check out this example on Hydra!](http://hydrashare.github.io/hydra/viewer?owner=' + gitUserName + '&fork=' + forkName + '&id=' + fileName + ')')
    readMeFile.write('\n')
    
    # Write change log in the file
    if len(changeLog) != 0:
        for line in changeLog:
            readMeFile.write(line + '\n')
    
    #Write in the file tags.
    readMeFile.write('### Tags \n')
    for linecount, line in enumerate(fileTags):
        if linecount+1 != len(fileTags): readMeFile.write(line + ', ')
        else: readMeFile.write(line)
    readMeFile.write('\n')
    
    #Write in a link to the thumbnail.
    readMeFile.write('### Thumbnail \n')
    readMeFile.write("![Screenshot](https://raw.githubusercontent.com/" + gitUserName + "/hydra/master/" + fileName + "/thumbnail.png)")
    readMeFile.write('\n')
    
    readMeFile.close()
    
    return readMeFilePath



def getAllTheComponents(document, onlyGHPython = False):
    components = []
    
    for component in document.Objects:
        if onlyGHPython and type(component)!= type(ghenv.Component): pass
        else: components.append(component)
    
    return components


def getMetaData(ghComps, fileTags, fileName, rhinoDocPath, additionalImgs):
    #Create the dictionary.
    metaDataDict = {}
    
    #Get the names of all of the components on the canvas and add them to the dictionary.
    metaDataDict["components"] = {}
    metaDataDict["images"] = []
    metaDataDict["videos"] = {}
    metaDataDict["dependencies"] = []
    
    grasshopperNative = ['Params', 'Maths', 'Sets', 'Vector', 'Curve', 'Surface', 'Mesh', 'Intersect', 'Transform', 'Display', 'Hydra']
    notImportantComps = ['Hydra', 'Scribble', 'Hydra_ExportFile', 'Hydra_ImportFile', 'Group', 'Panel', 'Slider', 'Boolean Toggle', 'Custom Preview', 'Colour Swatch','Button', 'Control Knob', 'Digit Scroller', 'MD Slider', 'Value List', 'Point', 'Vector', 'Circle', 'Circular Arc', 'Curve', 'Line', 'Plane', 'Rectangle', 'Box', 'Mesh', 'Mesh Face', 'Surface', 'Twisted Box', 'Field', 'Geometry', 'Geometry Cache', 'Geometry Pipeline', 'Transform']
    
    for component in ghComps:
        componentName = component.Name
        if componentName in notImportantComps: pass
        elif metaDataDict["components"].has_key(componentName):
            metaDataDict["components"][componentName] += 1
        else:
            metaDataDict["components"][componentName] = 1
        
        # find dependencies
        componentCategory = component.Category
        if componentCategory == "Extra" or componentCategory == "User":
                componentCategory = component.SubCategory
                
        if componentCategory not in grasshopperNative + metaDataDict["dependencies"]:
            metaDataDict["dependencies"].append(componentCategory)
            
    #Put in tags.
    metaDataDict['tags'] = fileTags
    
    # Put in the path to the gh scene image.
    metaDataDict["images"].append({fileName + '_GH.png' : "Grasshopper Definition"})
    
    # Put in the path to the rhino scene image.
    if not GHForThumb_:
        metaDataDict["images"].append({fileName + '_Rhino.png' : "Rhino Viewport Screenshot"})
    
    # add additional images to image list; at some point we should expose adding description for each image
    for img in additionalImgs:
        if os.path.isfile(img):
            metaDataDict["images"].append({os.path.split(img)[1] : "Additional Image"})
    
    # Put in the path to the thumbnail file.
    metaDataDict['thumbnail'] = 'thumbnail.png'
    
    # Put in the path to the zip file.
    metaDataDict['file'] = fileName + '.zip'
    
    
    return metaDataDict


def writeMetadataFile(fileName, repoTargetFolder, metaDataDict):
    jsonFilePath = repoTargetFolder + '\\' + 'input.json'
    with open(jsonFilePath, "w") as outfile:
        json.dump(metaDataDict, outfile)
    
    return jsonFilePath


def writeGHImage(fileName, repoTargetFolder):
    #Set the final File Path.
    filePathName = repoTargetFolder + '\\' + fileName + '_GH.png'
    
    #Take a tiled image using the GH Method.
    imageSettings = ghGUI.Canvas.GH_Canvas.GH_ImageSettings()
    canvas = ghInst.ActiveCanvas
    rect = gh.GH_Convert.ToRectangle(canvas.Document.BoundingBox(False))
    
    #System.Drawing.Rectangle 
    imgsOfCanvas = ghGUI.Canvas.GH_Canvas.GenerateHiResImage(canvas, rect, imageSettings)
    
    #This part is adapted and translated from David Rutten's VB script:
    # http://www.grasshopper3d.com/forum/topics/access-to-grasshopper-image-stitcher-ghis
    #Long live David!!!!
    
    #Prepare a large image to absorb the smaller images.
    tileWidth = 1000
    tileHeight = 1000
    width = int(str(imgsOfCanvas[-1]).split(',')[0].split('=')[-1])
    height = int(str(imgsOfCanvas[-1]).split(',')[-1].split('=')[-1].split('}')[0])
    smallImages = imgsOfCanvas[0]
    
    #If the image is too large, rezie it.
    if width > 16000 : width = 16000
    if height > 16000: height = 16000
    
    #Build the big image.
    fullImage = System.Drawing.Bitmap(width, height, System.Drawing.Imaging.PixelFormat.Format24bppRgb)
    fullFrame = System.Drawing.Rectangle(0, 0, tileWidth, tileHeight)
    fullGraphics = System.Drawing.Graphics.FromImage(fullImage)
    fullGraphics.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.NearestNeighbor
    fullGraphics.Clear(System.Drawing.Color.White)
    
    #Re-order the list of images to be correct
    newSmallImgDict = {}
    for image in smallImages:
        imageEnd = str(image).split('\\')[-1].split('.png')[0]
        imageHoriz = imageEnd.split(';')[0]
        imageVert = imageEnd.split(';')[-1]
        if not newSmallImgDict.has_key(imageHoriz) and int(imageHoriz) <= 15 and int(imageVert) <= 15: newSmallImgDict[imageHoriz] = [image]
        elif int(imageHoriz) <= 15 and int(imageVert) <= 15: newSmallImgDict[imageHoriz].append(image)
    
    #Join the smaller images into the larger images.
    fullFrame.Y = 0
    for columnNum in range(len(newSmallImgDict)):
        for rowNum in range(len(newSmallImgDict['0'])):
            #Select out the correct image.
            image = newSmallImgDict[str(columnNum)][rowNum]
            
            #Adjust the frame.
            #We need to move it right by tileWidth pixel
            #If the frame goes past the right, move it to the top of the next column.
            if fullFrame.Y >= height:
                fullFrame.Y = 0
                fullFrame.X += tileWidth
            
            #Now load the target image from the disk...
            targetImage = System.Drawing.Bitmap(image)
            
            #...and paint it into the target frame
            fullGraphics.DrawImage(targetImage, fullFrame)
            
            #Delete the targetImage from memory.
            targetImage.Dispose()
            
            fullFrame.Y += tileHeight
    
    
    #Save the image and dispose of it from memory.
    fullImage.Save(filePathName)
    fullGraphics.Dispose()
    
    return filePathName, fullImage, width, height


def writeRhinoImage(fileName, repoTargetFolder):
    viewtoCapture = sc.doc.Views.ActiveView  
    dispMode = viewtoCapture.ActiveViewport.DisplayMode
    image_h = viewtoCapture.ActiveViewport.Size.Height
    image_w = viewtoCapture.ActiveViewport.Size.Width
    viewSize = System.Drawing.Size(int(image_w), int(image_h))
    pic = rc.Display.RhinoView.CaptureToBitmap(viewtoCapture , viewSize)
    
    fullPath = repoTargetFolder + '\\' + fileName + '_Rhino.png'
    System.Drawing.Bitmap.Save(pic , fullPath)
    
    return fullPath, pic, image_w, image_h

def copyAddiationalImages(additionalImgs, repoTargetFolder):
    
    for img in additionalImgs:
        #chek if the file already exist
        if os.path.isfile(img):
            # copy to the file to the folder
            try:
                shutil.copyfile(img, repoTargetFolder + '\\' + os.path.split(img)[1])
            except:
               msg = "Failed to copy " + img
               print msg

def makeThumbnailImg(ghImgFile, rhinoImgFile, gw, gh, rw, rh, repoTargetFolder):
    #Set universal variables.
    thumbnailPath = repoTargetFolder + '\\' + 'thumbnail.png'
    thumbnailW = 200
    
    if GHForThumb_:
        #Calculate what the height should be.
        imgRatio = gh/gw
        thumbnailH = thumbnailW*imgRatio
        imgSize = System.Drawing.Size(thumbnailW, thumbnailH)
        imgHeight = ghImgFile.Height
        #Get the thumbnail image and save it
        fullImage = System.Drawing.Bitmap(ghImgFile,imgSize)
        System.Drawing.Bitmap.Save(fullImage , thumbnailPath)
    else:
        #Calculate what the height should be.
        imgRatio = rh/rw
        thumbnailH = thumbnailW*imgRatio
        imgSize = System.Drawing.Size(thumbnailW, thumbnailH)
        #Get the thumbnail image and save it
        fullImage = System.Drawing.Bitmap(rhinoImgFile,imgSize)
        System.Drawing.Bitmap.Save(fullImage , thumbnailPath)
    
    
    return thumbnailPath, fullImage


def main(fileName, fileDescription, fileTags, repoTargetFolder, doucumentPath, \
        document, rhinoDocPath, gitUserName, forkName, additionalImgs):
    #Write the GH file into a GHX file.
    ghFile = writeGHRhino(fileName, repoTargetFolder, doucumentPath, rhinoDocPath)
    
    #Take a high-res image of the grasshopper canvass.
    ghImgFile, ghImg, gw, gh = writeGHImage(fileName, repoTargetFolder)
    
    #Take an image of the Rhino scene
    if not GHForThumb_:
        rhinoImgFile, rhImg, rw, rh = writeRhinoImage(fileName, repoTargetFolder)
    else:
        rhImg, rw, rh = "", 1, 1
        
    #Make a thumbnail image.
    thumbnailImgFile, thumbnailImg = makeThumbnailImg(ghImg, rhImg, gw, gh, rw, rh, repoTargetFolder)
    
    #Clear the images from the computer memory.
    ghImg.Dispose()
    if not GHForThumb_:
        rhImg.Dispose()
    thumbnailImg.Dispose()    
    
    #Copy additional images to folder if any
    copyAddiationalImages(additionalImgs, repoTargetFolder)
    
    #Write the readMe into a text file.
    descriptFile = writeReadMe(fileName, fileDescription, repoTargetFolder, changeLog_, gitUserName, fileTags, forkName)
    
    #Get all of the components on the canvass and pull out their information so that they can be written into a metadata file.
    ghComps = getAllTheComponents(document)
    metaDataDict = getMetaData(ghComps, fileTags, fileName, rhinoDocPath, additionalImgs)
    metadataFile = writeMetadataFile(fileName, repoTargetFolder, metaDataDict)



if _export:
    if _fileName and len(_fileDescription) != 0:
        checkData, fileName, fileDescription, fileTags, repoTargetFolder, \
            doucumentPath, document, rhinoDocPath, gitUserName, forkName = checkTheInputs()
        
        if checkData == True:
            main(fileName, fileDescription, fileTags, repoTargetFolder, \
                doucumentPath, document, rhinoDocPath, gitUserName, \
                forkName, additionalImgs_)
    else:
        msg = "One of the mandatory inputs is missing!"
        print msg
        ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)