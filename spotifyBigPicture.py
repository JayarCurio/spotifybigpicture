import sys
import shutil
import tempfile
import zipfile
import re
import os
import argparse

WIN = 'win'
OSX = 'darwin'
LINUX = 'linux'
RESOURCES = 'Resources'
RESOURCES_ZIP = 'resources.zip'
RESOURCES_PATH_OSX = '/Applications/Spotify.app/Contents/' + RESOURCES
RESOURCES_PATH_LINUX = '/opt/spotify/spotify-client/Data/' + RESOURCES_ZIP
DEFAULT_FONT_SIZE = 8
PATTERN = 'size="([^"]*)"'

print '---[Spotify Big Picture]---'
parser = argparse.ArgumentParser()
parser.add_argument('-r', '--restore', help='Restore Spotify to default font size', action='store_true')
parser.add_argument('-s', '--size', type=int, help='The size fonts should be changed with (positive=up, negative=down)')
parser.add_argument('-p', '--path', help='Specify path to Spotify resources.zip/skin.xml if not detected automatically')
args = parser.parse_args()

def backupResources(resourcesPath):
    backupPath = resourcesPath + '.bak'
    print 'Creating backup of %s to %s' % (resourcesPath, backupPath)
    if os.path.exists(backupPath):
        print 'backup already exists'
    else:
        shutil.copy2(resourcesPath, backupPath)

def restoreResources(resourcesPath):
    backupPath = resourcesPath + '.bak'
    print 'restoring default font size from backup %s' % backupPath
    if os.path.exists(backupPath):
        os.remove(resourcesPath)
        os.rename(backupPath, resourcesPath)
    else:
        print 'No backup file found, restore not possible'

def extractArchive(resourcesPath):
    extractDir = tempfile.mkdtemp()
    print 'extracting %s to %s' % (resourcesPath, extractDir)
    zf = zipfile.ZipFile(resourcesPath, 'r')
    try:
        for name in zf.namelist():
            zf.extract(name, extractDir)
    finally:
        zf.close()
    return extractDir

def compressArchive(srcDir, resourcesPath):
    print 'compressing files from %s to %s' % (srcDir, resourcesPath)
    zf = zipfile.ZipFile(resourcesPath, mode='w')
    try:
        for root, dirs, files in os.walk(srcDir):
            for filename in files:
                absName = os.path.join(root, filename)
                arcName = absName[len(srcDir) + 1:]
                zf.write(absName, arcname=arcName)
    finally:
        zf.close()

def getXmlFiles(resourcesPath):
    xmlFiles = list()
    xmlFiles.append(resourcesPath + '/skin.xml')
    for root, dirs, files in os.walk(resourcesPath + '/views'):
        for f in files:
            xmlFiles.append(os.path.join(root, f))
    return xmlFiles

def modifyXmlFiles(resourcesPath, fontSize):
    fileList = getXmlFiles(resourcesPath)
    for xmlFile in fileList:
        print 'updating %s with font size %s' % (xmlFile, fontSize)
        newXmlFile = xmlFile + '.new'
        reg = re.compile(PATTERN)
        with open(xmlFile, 'r') as infile:
            with open(newXmlFile, 'w') as outfile:
                for line in infile:
                    value = reg.search(line)
                    if value is not None:
                        oldSize = value.group(1)
                        newSize = int(oldSize) + fontSize
                        line = re.sub(reg, 'size="' + str(newSize) + '"', line)
                    outfile.write(line)
        os.remove(xmlFile)
        os.rename(newXmlFile, xmlFile)

def getResourcesPathForWindows():
    import _winreg
    key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Spotify")
    value = _winreg.QueryValueEx(key, "")[0]
    return value + '\\Data\\resources.zip'

if args.restore:
    if args.path:
        if args.path.endswith(RESOURCES_ZIP) or args.path.endswith(RESOURCES):
            restoreResources(args.path)
        else:
            print 'File not recognized, must be either %s or%s' % (RESOURCES_ZIP, RESOURCES)
            exit(0)
    elif sys.platform.startswith(LINUX):
        restoreResources(RESOURCES_PATH_LINUX)
    elif sys.platform == OSX:
        restoreResources(RESOURCES_PATH_OSX)
    elif sys.platform.startswith(WIN):
        restoreResources(getResourcesPathForWindows())
    else:
        print 'OS not recognized, use --path <file path> to manually specify the resources.zip or skin.xml'
        exit(0)
else:
    fontSize = DEFAULT_FONT_SIZE
    if args.size:
        fontSize = args.size

    if args.path:
        if args.path.endswith(RESOURCES_ZIP):
            backupResources(args.path)
            extractedDir = extractArchive(args.path)
            modifyXmlFiles(extractedDir, fontSize)
            compressArchive(extractedDir, args.path)
        elif args.path.endswith(RESOURCES):
            backupResources(args.path)
            modifyXmlFiles(args.path, fontSize)
        else:
            print 'File not recognized, must be either %s or%s' % (RESOURCES_ZIP, RESOURCES)
            exit(0)
    else:
        if sys.platform.startswith(LINUX):
            backupResources(RESOURCES_PATH_LINUX)
            extractedDir = extractArchive(RESOURCES_PATH_LINUX)
            modifyXmlFiles(extractedDir, fontSize)
            compressArchive(extractedDir, RESOURCES_PATH_LINUX)
        elif sys.platform == OSX:
            backupResources(RESOURCES_PATH_OSX)
            modifyXmlFiles(RESOURCES_PATH_OSX, fontSize)
        elif sys.platform.startswith(WIN):
            filePath_windows = getResourcesPathForWindows()
            backupResources(filePath_windows)
            extractedDir = extractArchive(filePath_windows)
            modifyXmlFiles(extractedDir, fontSize)
            compressArchive(extractedDir, filePath_windows)
        else:
            print 'OS not recognized, use --path <file path> to manually specify the resources.zip or skin.xml'
            exit(0)
print 'Done'
