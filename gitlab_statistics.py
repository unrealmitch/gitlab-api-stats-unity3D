
# -*- coding: utf-8 -*-

import re

unityscript =   [ ".cs" ]
unityshader =   [ ".shader", ".cginc", ".hlsl" ]
unityscene =    [ ".unity", ".scene" ]
unityprefab =   [ ".prefab", ".variant" ]
unityfile =     [ ".asset", ".mat", ".anim", ".physicsMaterial2D", ".physicMaterial", ".controller" ]
unitymeta =     [ ".meta" ]
mediafile =     [ 
".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tga", ".psd", ".svg", ".ai", ".eps", ".tiff",
".mp3", ".wav", ".ogg", 
".mp4", ".mov", ".avi", ".m4v", ".wmv", ".flv", ".swf", ".webm", ".ogv", ".mpg", ".mpeg", ".m4p", ".m4v", ".m4a", ".m4b", ".m4r", ".m4v", ".3gp"
]
modelfile =     [ 
".obj", ".fbx", ".glb", ".gltf" ".blend", ".max", ".dxf", ".3ds", ".c4d",
".ply", ".stl", ".x", ".x3d", ".ply", ".dae", ".usd", ".usdz", ".lwo", ".abc", ".3dm"
]
txtFiles =      [ 
".json", ".yml", ".package", ".txt", ".md", ".indd", ".pdf", ".doc", 
".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".xd", ".gitignore", ".readme"
]
scripts =       [ 
".c" , ".cpp", ".js", ".html", ".py", ".pyc", ".java", ".sh", ".bat", ".css", ".class", ".h", ".php",
".cgi", ".pl", ".htm", ".vb", ".swift", ".go", ".ino", ".pde", ".lua", ".vue"
]

filefilters = {
    "cs" : unityscript,
    "cg" : unityshader,
    "sc" : unityscene,
    "pf" : unityprefab,
    "fl" : unityfile,
    "mt" : unitymeta,
    "mf" : mediafile,
    "md" : modelfile,
    "ol" : scripts,
    "tx" : txtFiles
}

# FC:Files Changed, TC:Total Changes (@@ .. @@), TA:Total Adds, TD:Total Deletes, LA:Total Add Lines, LD: Total Delete Lines
def GetMoreStateDic():
    dict = {}
    for key in filefilters:
        dict[key] = [0, 0, 0, 0, 0, 0]
    dict["o"] = [0, 0, 0, 0, 0, 0]

    return dict


def GetStatsFileGroup(filename):
    if("." in filename):
        filename = "." + filename.split(".")[-1].lower()
        for key, value in filefilters.items():
            if(filename in value):
                return key
        return "o"
    else:
        return "o"

def GetMoreStatsDiff(diff):
    if(diff == "" or len(diff) < 5):
        return (0,0,0,0)
    else:
        occr = re.findall(r"@@ .* @@", diff)
        changes = 0
        adds = 0
        dels = 0
        addchar = 0
        delchar = 0

        for line in occr:
            changes += 1
            lineClean = line.replace("@","").strip()
            for change in lineClean.split(" "):
                if(change.startswith("+")):
                    val = int(change.split(",")[-1])
                    if(val > 0):
                        adds += 1
                        addchar += val
                if(change.startswith("-")):
                    val = int(change.split(",")[-1])
                    if(val > 0):
                        dels += 1
                        delchar += val

        return (changes,adds,dels,addchar,delchar)