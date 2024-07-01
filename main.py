import datetime
start = datetime.datetime.now()
print("\x1b[32m__ READING __\x1b[0m")

import json
import sys
import shlex
import wave
import os
import re
import random
from zipfile import ZipFile
import shutil


inputfile = open(sys.argv[2], "r").read()
outputfile = "output/project.json"
output = {"targets": [], "monitors": [], "extensions": [], "meta": {
    "semver": "3.4.0", "vm": "2.3.0", "agent": "Thanks for using CatSh ❤️"}}
var = {}
lists = {}
totalblocks = 0
totaltargets = 0
totalvariables = 0
totalsounds = 0
totalcostumes = 0
blocks = {}
blocksbyid = {}
varsbyid = {}
g = [[False,""]]
v = False
currentsprite = None
assets = []
iscomment = 0
isquoted = False
warnings = []

def makeInputs(block,target,blockname,keys,field):
        global blocksbyid, totalblocks
        if block[2] == blockname:
            outputs = {}
            fields = {}
            for i in range(len(keys)):
                try:
                    if keys[i] == "SPECIAL.BLOCK":
                        outputs["SUBSTACK"] = [2,block[3+i].strip('"')]
                    elif keys[i] == "SPECIAL.BLOCK2":
                        outputs["SUBSTACK2"] = [2,block[3+i].strip('"')]
                    elif block[3+i].strip('"')[0:3] == "blk":
                        outputs[keys[i]] = [2,blocksbyid[block[3+i].strip('"')]]
                    else:
                        outputs[keys[i]] = [1,[10,block[3+i].strip('"')]]
                except IndexError:
                    warnings.append(f"Failed to read parameter {i+1} for block {totalblocks} ({block[2]})")
            for i in range(len(field)):
                fields[field[i]] = [block[3+i+len(keys)].strip('"'),None]
            output["targets"][target]["blocks"][f"""{blocksbyid[f'blk{totalblocks}']}"""]["inputs"] = outputs

def varEval(block,target):
    try:
        orgblock = block
        block = shlex.split(block)
        if len(block) < 1:
            return
        if block[0] != "define" and block[0] != "import":
            a = output["targets"][target]["blocks"][f"{blocks[orgblock]}"]["inputs"]
            for key in a:
                c = a[key][1][1]
                vn = c[1:-1]
                if c[0] == "<" and c[-1] == '>':
                    output["targets"][target]["blocks"][f"{blocks[orgblock]}"]["inputs"][key] = [3, [12,vn,varsbyid[vn]],[4,"0"]]

    except Exception as e:
            print(e)

    
def blockEval(block, target):
    orgblock = block
    global totalblocks, totalvariables,totalcostumes,blocks,blocksbyid
    block = shlex.split(block)
    if len(block) < 1:
        return
    assetId = ''.join(random.choice('0123456789abcdefABCDEF') for _ in range(32))
    blocks[orgblock] = ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ[]-!*{}') for _ in range(32-len(str(totalblocks+1)))) + str(totalblocks+1)
    blocksbyid[f"blk{totalblocks+1}"] = blocks[orgblock]
    if block[0] == "define":
        print(f"➡️  \x1b[35mCreated new {block[1]}\x1b[0m: {block[2]} = {block[4]}")
        if block[1] == "var":
            totalvariables += 1
            
            varsbyid[block[2]] = f'var{totalvariables}'

            output["monitors"].append({"id": f"var{totalvariables}", "mode": "default", "opcode": "data_variable", "params": {"VARIABLE": block[2]}, "value": block[4],"spritename":None,"width":0,"height":0,"x":0,"y":0,"visible":False,"sliderMin":0,"sliderMax":100,"isDiscrete":True})
            output["targets"][0]["variables"][f"""var{totalvariables}"""] = [block[2], block[4]]
    elif block[0] == "import":
        print(f"➡️  \x1b[35mImported {block[1]}\x1b[0m: {block[2]}")
        assets.append([block[2],assetId+'.'+block[1]])
        if block[1] == "png":
            output["targets"][target]["costumes"].append({"name": block[2].split(".")[0], "dataFormat": "png", "assetId": assetId, "md5ext": assetId+'.png', "rotationCenterX": 240, "rotationCenterY": 180})
        if block[1] == "svg":
                output["targets"][target]["costumes"].append({"name": block[2].split(".")[0], "dataFormat": "svg", "assetId": assetId, "md5ext": assetId+'.svg', "rotationCenterX": 240, "rotationCenterY": 180})
        if block[1] == "wav":
                wav = wave.open(block[2], 'rb')
                rate = wav.getframerate()
                sample_count = wav.getnframes()
                output["targets"][target]["sounds"].append({"name": block[2].split(".")[0], "dataFormat": "wav", "assetId": assetId, "md5ext": assetId+'.wav', "sampleCount": sample_count, "rate": rate})
                totalcostumes += 1
    else:
        print(f"\x1b[34m{nm}\x1b[0m/{startline}/{totalblocks+1}: {g[len(g)-1][1]}")
        totalblocks += 1

        output["targets"][target]["blocks"][f"""{blocks[orgblock]}"""] = {"opcode": block[2], "next": f"blk{block[1]}" if block[1] != "-1" else None,"parent":f"blk{block[0]}" if block[0] != "-1" else None,"fields":{},"inputs":{},"shadow":False,"topLevel":True}
        
        with open("blocks.py") as f:
            f = f.read().split('\n')[1:]
            f = '\n'.join(f)
            exec(f)
        
if sys.argv[1] == 'convert':
    for f in range(len(inputfile)):
        i = inputfile[f]
        if inputfile[f:f+2] == '/*':
            iscomment = 1
        elif inputfile[f:f+2] == '*/' and iscomment == 1:
            iscomment = 0
        if inputfile[f] == '#':
            iscomment = 2
        if inputfile[f] == '\n' and iscomment == 2:
            iscomment = 0
        if inputfile[f] == '"':
            #g[len(g)-1][1] += i
            isquoted = not isquoted
        if isquoted:
            g[len(g)-1][1] += i
        if iscomment == 0 and not isquoted:
            if i == ":":
                print("🧍 processing sprite: ",end='')
                currentsprite = totaltargets
                nm = ""
                sn = inputfile[f+1]
                sni = 1
                while sn != ".":
                    nm += sn
                    sni += 1
                    sn = inputfile[f+sni]
                if nm != "Stage":
                    isStage = False
                    output["targets"].append(
                        {"name": nm, "isStage": isStage, "blocks": {}, "comments": {}, "broadcasts": {}, "lists": {}, "variables": {},"sounds":[], "volume": 100, "layerOrder": totaltargets, "visible": True, "x": 0, "y": 0, "size": 100, "direction": 90, "draggable": False, "rotationStyle": "all around","costumes":[]})
                else:
                    isStage = True
                    output["targets"].append(
                    {"name": nm, "isStage": isStage, "blocks": {}, "lists": {}, "broadcasts": {}, "variables": {}, "comments": {}, "currentCostume": 0, "costumes": [], "sounds": [], "volume": 100, "layerOrder": 0, "tempo": 60})

                totaltargets += 1
                print(f"\x1b[34m{nm}\x1b[0m")
            if i == ';':
                currentsprite = None
        
            if i == "{":
                startline = inputfile[:f].count('\n') + 1
                g.append([True,""])
            elif g[len(g)-1][0] is True:
                if i == "}":
                    if startline == inputfile[:f].count('\n') + 1:
                        startline = str(startline)
                    else:
                        startline = f"{startline}-{inputfile[:f].count('\n') + 1}"
                    blockEval(g[len(g)-1][1], currentsprite)
                    g.pop(-1)
                    continue
                g[len(g)-1][1] += i
    print("🔍 Checking for \x1b[33mvariables\x1b[0m...")
    g = [[False,'']]
    totaltargets = 0
    for f in range(len(inputfile)):
        i = inputfile[f]
        if i == ":":
            currentsprite = totaltargets
            totaltargets+=1
        if i == ';':
            currentsprite = None
        if i == "{":
            g.append([True,""])
        elif g[len(g)-1][0] is True:
            if i == "}":
                g.pop(-1)
                continue
            g[len(g)-1][1] += i
        if i == "<":
            varname = ""
            v = True
        elif v is True:
            if i == ">":
                print(f"\x1b[33mvariable\x1b[0m reference for \x1b[33m<{varname}>\x1b[0m inside block #{totalblocks}")
                varEval(g[len(g)-1][1],currentsprite,v)
                v = False
                continue
            varname += i

    hasStage = False
    for i in output["targets"]:
        if i["isStage"]:
            hasStage = True
        if i["costumes"] == []:
            warnings.append(f"{i['name']} has no costume 👻!")
    if not hasStage:
        warnings.append("No stage found. 📋")
    
    
    print("\x1b[32m__ WRITING __\x1b[0m")
    assetsNew = []

    print("🔍 Checking if output dir exists")
    if not os.path.exists("output/"):
        print("making output dir")
        os.system("mkdir output")
    else:
        print("💣 Clearing output dir")
        os.system("rm output/* -rf")
    if os.path.exists("output.sb3"):
        print("💣 Clearing zip (.sb3)")
        os.system("rm output.sb3")
    print("📁 Copying assets to output folder")
    for i in range(len(assets)):
        os.system(f"cp {assets[i][0]} output/{assets[i][1]}")
        assetsNew.append(assets[i][1])
    
    print("⬇️  Dumping JSON")
    g = json.dumps(output,indent=4)
    
    print("❓ Generating random IDs")
    for i in range(totalblocks):
        g = g.replace(f'blk{i+1}',blocksbyid[f'blk{i+1}'])

    print("✍️  writing json to outputfile")
    open(outputfile,'w').write(g)
    if not os.path.exists('output.sb3'):
        with open('output.zip', 'w') as fp:
            fp.write('')
    
    print("📦 Packaging into .sb3")
    with ZipFile('output.zip',mode='w') as zipf:
        for root, dirs, files in os.walk('output'):
            for file in files:
            # Construct the full file path
                file_path = os.path.join(root, file)
            # Add the file to the ZIP file
                zipf.write(file_path, arcname=os.path.relpath(file_path, 'output'))
    shutil.move('output.zip','output.sb3')

    end = datetime.datetime.now()
    print("\x1b[32m__ STATUS __\x1b[0m")
    if len(warnings) > 0:
        print(f'\x1b[31m🚫 {len(warnings)} Warning{'' if len(warnings) == 1 else ''} Occured:')
        for warning in warnings:
            print(" 🚫 Warning! " + warning)
    else:
        print("\x1b[32m✅ No Warnings")
    print('\x1b[0m',end='')
    print('📦 Convertd in ' + str((end-start)))


