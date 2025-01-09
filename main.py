import datetime
import json
import argparse
import random
import shlex
import wave
import os
import shutil
from PIL import Image
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from exceptions import * 
from blocks import blockargs

start = datetime.datetime.now()


def is_numeric(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


global parser


def autotype(s):
    if s.lower() == "true":
        return True
    elif s.lower() == "false":
        return False
    try:
        return float(s)
    except ValueError:
        pass
    try:
        return int(s)
    except ValueError:
        pass
    return s


class Block:
    def __init__(self, things: list, child: bool | list = False):
        if args.verbose:
            print(str(parser.spriteblocks+1) + " " + " ".join(things))
        if isinstance(child, list):          
            self.init_child(things, child)
        elif is_numeric(things[0]) or things[0] == "p":
            self.init_numeric(things, child)
        else:
            self.init_asset(things)

    def init_numeric(self, things, child):
        parser.totalblocks += 1
        parser.spriteblocks += 1
        if isinstance(child, bool) and not child:
            self.ischild = False
            if things[0] == "p":
                things[0] = str(parser.spriteblocks-1)
            if things[1] == "n":
                things[1] = str(parser.spriteblocks+1)
            self.parent = things[0]
            self.child = things[1]
            self.opcode = things[2]
            self.opsection = things[2][:things[2].index("_")]
            self.blockid = f"spr{parser.cursprite}blk{parser.spriteblocks}"
            self.arguments = things[3:]
            self.inputs = {}
            self.fields = {}
            self.embryos = 0
            if things[2] in ["event_whenflagclicked"]:
                print("x")
                self.x = random.randint(0,1000)
                self.y = random.randint(0,1000)
        self.args()

    def init_child(self, things, child):
        parser.totalblocks += 1
        self.ischild = True
        self.parent = child[2].blockid
        self.child = None
        self.opcode = things[0]
        self.opsection = things[0][:things[0].index("_")]
        self.blockid = f"spr{parser.cursprite}blk{parser.spriteblocks}chl{child[2].embryos}"
        self.arguments = things[1:]
        self.inputs = {}
        self.fields = {}
        self.embryos = child[2].embryos
        if things[0] in ["event_whenflagclicked"]:
            print("x")
            self.x = random.randint(0,1000)
            self.y = random.randint(0,1000)
        self.args()

    def init_asset(self, things):
        self.assetId = "".join(random.choice("0123456789abcdefABCDEF") for _ in range(32))
        if things[0] == "config":
            self.handle_config(things)
        elif things[0] == "import":
            self.handle_import(things)
        elif things[0] == "define":
            self.handle_variable(things)

    def handle_variable(self, things):
        if not len(things) >= 5:
            raise CatShException("Invalid variable definition")
        if things[1] == "var":
            self.handle_var_definition(things)
        elif things[1] == "list":
            self.handle_list_definition(things)
        parser.variables += 1
        parser.varnames.append(things[2])
        for i in things[5:]:
            if "=" in i:
                i = i.split("=")
                if i[0] not in output["monitors"][-1]:
                    raise InvalidArgumentError()
                else:
                    output["monitors"][-1][i[0]] = autotype(i[1])

    def handle_var_definition(self, things):
        if things[4] == "global":
            self.add_global_var(things)
        elif things[4] == "local":
            self.add_local_var(things)
        else:
            raise CatShException("Invalid variable definition")

    def handle_list_definition(self, things):
        if things[4] == "global":
            self.add_global_list(things)
        elif things[4] == "local":
            self.add_local_list(things)
        else:
            raise CatShException("Invalid variable definition")

    def add_global_var(self, things):
        output["monitors"].append({
            "id": f"var{parser.variables}",
            "mode": "default",
            "opcode": "data_variable",
            "params": {"VARIABLE": things[2]},
            "value": things[3],
            "spritename": None,
            "width": 0,
            "height": 0,
            "x": 0,
            "y": 0,
            "visible": False,
            "sliderMin": 0,
            "sliderMax": 100,
            "isDiscrete": True,
        })
        output["targets"][0]["variables"][f"var{parser.variables}"] = [things[2], things[3]]

    def add_local_var(self, things):
        output["monitors"].append({
            "id": f"var{parser.variables}",
            "mode": "default",
            "opcode": "data_variable",
            "params": {"VARIABLE": things[2]},
            "value": things[3],
            "spritename": parser.cursprite - 1,
            "width": 0,
            "height": 0,
            "x": 0,
            "y": 0,
            "visible": False,
            "sliderMin": 0,
            "sliderMax": 100,
            "isDiscrete": True,
        })
        output["targets"][parser.cursprite - 1]["variables"][f"var{parser.variables}"] = [things[2], things[3]]

    def add_global_list(self, things):
        output["monitors"].append({
            "id": f"var{parser.variables}",
            "mode": "list",
            "opcode": "data_listcontents",
            "params": {"LIST": things[2]},
            "spritename": None,
            "value": json.loads(things[3]),
            "width": 0,
            "height": 0,
            "x": 0,
            "y": 0,
            "visible": False,
        })
        output["targets"][0]["lists"][f"var{parser.variables}"] = [things[2], json.loads(things[3])]

    def add_local_list(self, things):
        output["monitors"].append({
            "id": f"var{parser.variables}",
            "mode": "list",
            "opcode": "data_listcontents",
            "params": {"LIST": things[2]},
            "spritename": parser.cursprite - 1,
            "value": json.loads(things[3]),
            "width": 0,
            "height": 0,
            "x": 0,
            "y": 0,
            "visible": False,
        })
        output["targets"][parser.cursprite - 1]["lists"][f"var{parser.variables}"] = [things[2], json.loads(things[3])]

    def handle_config(self, things):
        if things[1] in ["volume", "visible", "x", "y", "size", "direction", "draggable", "rotationStyle"]:
            output["targets"][parser.cursprite - 1][things[1]] = autotype(things[2])

    def handle_import(self, things):
        things[2] = things[2][1:-1]
        importas = things[4] if len(things) == 5 and things[3] == "as" else things[2].split(".")[0].split("/")[-1].split("\\")[-1]
        if things[1] in ["png", "jpg", "svg"]:
            self.import_image(things, importas)
        elif things[1] in ["mp3", "wav", "ogg"]:
            self.import_sound(things, importas)
        else:
            raise UnknownAssetTypeError(things[1])

    def import_image(self, things, importas):
        path = os.path.join(args.pwd, things[2]) if os.path.dirname(things[2]) != "special" else things[2]
        rotc = self.get_rotation_center(path, things[1])
        parser.assets.append([path, f"{self.assetId}.{things[1]}"])
        output["targets"][parser.cursprite - 1]["costumes"].append({
            "name": importas,
            "dataFormat": things[1],
            "assetId": self.assetId,
            "md5ext": f"{self.assetId}.{things[1]}",
            "rotationCenterX": rotc[0],
            "rotationCenterY": rotc[1],
        })

    def get_rotation_center(self, path, format):
        if format == "svg":
            tree = ET.parse(path)
            root = tree.getroot()
            return [float(root.attrib["width"]) / 2, float(root.attrib["height"]) / 2]
        else:
            im = Image.open(path)
            return [im.size[0] / 2, im.size[1] / 2]

    def import_sound(self, things, importas):
        parser.assets.append([things[2], f"{self.assetId}.{things[1]}"])
        path = os.path.join(args.pwd, things[2]) if os.path.dirname(things[2]) != "special" else things[2]
        wav = wave.open(path, "rb")
        rate = wav.getframerate()
        sample_count = wav.getnframes()
        output["targets"][parser.cursprite - 1]["sounds"].append({
            "name": importas,
            "dataFormat": things[1],
            "assetId": self.assetId,
            "md5ext": f"{self.assetId}.{things[1]}",
            "sampleCount": sample_count,
            "rate": rate,
        })

    def args(self):
        inputs = self.arguments[:len(blockargs[self.opsection][self.opcode])-1]
        fields = self.arguments[len(blockargs[self.opsection][self.opcode])-1:]
        if len(inputs) > 0:
            self.process_inputs(inputs)
        if len(fields) > 0:
            self.process_fields(fields)
        self.update_output()

    def process_inputs(self, inputs):
        expected_inputs = len(blockargs[self.opsection][self.opcode][0])
        if len(inputs) < expected_inputs-1:
            raise NotEnoughArgsError(self.blockid, "Inputs", expected_inputs, len(inputs))
        for i, input_value in enumerate(inputs[:expected_inputs]):
            blockargsi = blockargs[self.opsection][self.opcode][0][i].upper()
            block = parser.mini_get_between(input_value, "[", "]")
            var = parser.mini_get_between(input_value, "<", ">")
            if block:
                self.handle_block(block, blockargsi)
            elif var:
                self.handle_var(var, blockargsi)
            elif input_value.startswith("blk") and is_numeric(input_value[3:]):
                self.handle_block_reference(input_value[3:], blockargsi)
            elif blockargsi == "KEY_OPTION": # is key pressed block
                self.embryos += 1
                self.inputs[blockargsi] = [1, f"spr{parser.cursprite}blk{parser.spriteblocks}chl{self.embryos}"]
                output["targets"][parser.cursprite - 1]["blocks"][f"spr{parser.cursprite}blk{parser.spriteblocks}chl{self.embryos}"] = {
					"opcode": "sensing_keyoptions",
					"next": None,
					"parent": f"spr{parser.cursprite}blk{parser.spriteblocks}",
					"inputs": {},
					"fields": { "KEY_OPTION": [input_value, None] },
					"shadow": True,
					"topLevel": False,
				}
            else:
                self.inputs[blockargsi] = [1, [10, input_value]]

    def process_fields(self, fields):
        expected_fields = len(blockargs[self.opsection][self.opcode][1])
        if len(fields) < expected_fields-1:
            raise NotEnoughArgsError(self.blockid, "Fields", blockargs[self.opsection][self.opcode][1], fields)
        for i, field_value in enumerate(fields[:-1]):
            blockargsi = blockargs[self.opsection][self.opcode][1][i].upper()
            block = parser.mini_get_between(field_value, "[", "]")
            if blockargsi == "VARIABLE":
                try:
                    self.fields[blockargsi] = [3, [12, field_value, parser.varnames.index(field_value)], [4, "0"]]
                except:
                    self.fields[blockargsi] = [1, [10, field_value]]
            elif block:
                self.handle_block(block, blockargsi, True)
            elif field_value.startswith("blk") and is_numeric(field_value[3:]):
                self.handle_block_reference(field_value[3:], blockargsi, True)
            else:
                self.fields[blockargsi] = [1, [10, field_value]]

    def handle_var(self, varname, blockargsi, is_field=False):
        target = self.fields if is_field else self.inputs
        target[blockargsi] = [3, [12, varname, f"var{parser.varnames.index(varname)}"], [4, "0"]]

    def handle_block_reference(self, _id, blockargsi, is_field=False):
        target = self.fields if is_field else self.inputs
        target[blockargsi] = [3, f"spr{parser.cursprite}blk{_id}", [4, ""]]

    def handle_block(self, block, blockargsi, is_field=False):
        self.embryos += 1
        block = parser.mini_join_between(shlex.split(block), "[", "]")
        Block(block, [True, self.blockid, self])
        target = self.fields if is_field else self.inputs
        target[blockargsi] = [3, f"spr{parser.cursprite}blk{parser.spriteblocks}chl{self.embryos}", [4, ""]]

    def update_output(self):
        par = self.parent if self.parent.startswith("spr") else f"spr{parser.cursprite}blk{self.parent}" if self.parent not in ["-1", None] else None
        output["targets"][parser.cursprite - 1]["blocks"][self.blockid] = {
            "opcode": self.opcode,
            "parent": par,
            "next": f"spr{parser.cursprite}blk{self.child}" if self.child not in ["-1", None] else None,
            "fields": self.fields,
            "inputs": self.inputs,
            "shadow": False,
            "topLevel": True,
        }
        if hasattr(self,"x"):
            print("x")
            output["targets"][parser.cursprite - 1]["blocks"][self.blockid]["x"] = self.x
            output["targets"][parser.cursprite - 1]["blocks"][self.blockid]["y"] = self.y


class Parser:
    def __init__(self, string):
        self.value = string
        self.i = -1
        self.cursprite = 0
        self.sprite = [""]
        self.assets = []
        self.blocks = []
        self.isquoted = False
        self.totalblocks = 0
        self.spriteblocks = 0
        self.variables = 0
        self.varnames = []

    def move(self, amount):
        self.i += amount

    def get_index(self, additional=None):
        if additional == None:
            x = self.value[self.i]
        else:
            x = self.value[self.i : self.i + additional]
        return x

    def get(self, other):
        if self.isquoted:
            if self.value[self.i] == '"':
                self.isquoted = not self.isquoted
            else:
                self.move(1)
                return False
        if self.get_index(len(other)) == other:
            self.move(len(other) + 1)
            return True
        else:
            return False

    def get_to(self, other, offset=0):
        start = self.i + offset
        if self.isquoted:
            end = self.value.find('"', start)
            if end == -1:
                return self.value[start:]
            self.i = end + 1
            return self.value[start:end]
        end = self.value.find(other, start)
        if end == -1:
            return self.value[start:]
        self.i = end + len(other)
        return self.value[start:end]

    def get_between(self, one, two):
        if isinstance(one,list):
            for i in one:
                if self.get(i):
                    self.move(-1)
                    value = self.get_to(two)
                    return value
        else:
            if self.get(one):
                self.move(-1)
                value = self.get_to(two)
                return value

    def mini_get_between(self, orgstr, one, two):
        start = orgstr.find(one)
        if start == -1:
            return ""
        start += len(one)
        end = orgstr.rfind(two, start)
        if end == -1:
            return orgstr[start:]
        return orgstr[start:end]

    def mini_join_between(self, lst, one, two):
        new = []
        is_in = False
        temp = []
        count = 0
        for i in lst:
            if not is_in:
                if i.startswith(one):
                    temp.append(i)
                    is_in = True
                    count += 1
                else:
                    new.append(i)
            else:
                if i.endswith(two):
                    temp.append(i)
                    count -= 1
                    if count == 0:
                        new.append(" ".join(temp))
                        temp = []
                        is_in = False
                else:
                    temp.append(i)
        return new

    def getcur(self):
        return self.value[self.i - 1]


ap = argparse.ArgumentParser("CatSh", "Programming language for scratch.mit.edu")
ap.add_argument("input", help="Input file")
ap.add_argument("-c","--pwd", help="Directory where files are at",default="./")
ap.add_argument("-o", "--output", help="Output file", default="o.sb3")
ap.add_argument(
    "-a", "--action", help="Action to perform", choices=["convert", "convert_back"]
)
ap.add_argument("-v","--verbose",action="store_true")
args = ap.parse_args()

output = {
    "targets": [],
    "monitors": [],
    "extensions": [],
    "meta": {"semver": "3.4.0", "vm": "2.3.0", "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"},
}

try:
    with open(os.path.join(args.pwd, args.input)) as f:
        inputfile = f.read()
        parser = Parser(inputfile)
        while parser.i < len(parser.value):
            parser.move(1)
            parser.get_between("//", "\n")
            if parser.get(";"):
                parser.cursprite = 0
            sprite = parser.get_between("sprite ", ":")
            if sprite:
                if parser.sprite[parser.cursprite] != "":
                    raise SpriteInSpriteError()
                sprite = sprite.rstrip().lstrip()
                parser.sprite.append(sprite)
                parser.cursprite = len(parser.sprite) - 1
                parser.spriteblocks = 0
                if sprite == "Stage":
                    output["targets"].append(
                        {
                            "name": sprite,
                            "isStage": True,
                            "blocks": {},
                            "lists": {},
                            "broadcasts": {},
                            "variables": {},
                            "comments": {},
                            "currentCostume": 0,
                            "costumes": [],
                            "sounds": [],
                            "volume": 100,
                            "layerOrder": 0,
                            "tempo": 60,
                        }
                    )
                    if len(output["targets"]) - 1 != 0:
                        raise StageNotFirstError()
                elif sprite == "":
                    raise NoSpriteNameError()
                else:
                    output["targets"].append(
                        {
                            "name": sprite,
                            "isStage": False,
                            "blocks": {},
                            "comments": {},
                            "broadcasts": {},
                            "lists": {},
                            "variables": {},
                            "sounds": [],
                            "volume": 100,
                            "layerOrder": len(sprite),
                            "visible": True,
                            "x": 0,
                            "y": 0,
                            "size": 100,
                            "direction": 90,
                            "draggable": False,
                            "rotationStyle": "all around",
                            "costumes": [],
                        }
                    )
            block = parser.get_between("{","}")
            if block:
                if parser.cursprite == 0:
                    raise NoSpriteError()
                block = shlex.split(block,posix=False)
                if block[0] not in ["define","config","import"]:
                    Block(parser.mini_join_between(block, "[", "]"))
                else:
                    Block(block)
                parser.move(-1)
    hasStage = False
    for i in output["targets"]:
        if i["isStage"]:
            hasStage = True
        if i["costumes"] == []:
            raise NoCostumesError(i["name"])
    if not hasStage:
        raise NoStageError()
    assetsNew = []
    if not os.path.exists("output/"):
        os.mkdir("output")
    else:
        shutil.rmtree("output")
        os.mkdir("output")
    if os.path.exists("output.sb3"):
        os.remove("output.sb3")
    for i in range(len(parser.assets)):
        shutil.copy(parser.assets[i][0], f"output/{parser.assets[i][1]}")
        assetsNew.append(parser.assets[i][1])
    output_json = json.dumps(output, indent=4)

    with open("output/project.json", "w") as f:
        f.write(output_json)

    with ZipFile("output.zip", mode="w") as zipf:
        for root, dirs, files in os.walk("output"):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=os.path.relpath(file_path, "output"))
    shutil.move("output.zip", args.output)
except Exception as e:
    if hasattr(e, "isCatSh"):
        print("CatSh Error: " + e.message)
        exit()
    else:
        raise e


end = datetime.datetime.now()
print(f"Converted in {end-start}")
