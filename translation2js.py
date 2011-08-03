# -*- coding: utf-8 -*-

import os , sys

# getting path for the input-file empty.js
try:
    if len(sys.argv) != 2:
         print "You have to specify the Path to the directory i18n containing empty.js"
         print "python translation2js.py <path to directory i18n>"
         sys.exit()
    Path2emptyjs = sys.argv[1]
except:
        sys.exit()


try:
    import yaml
except ImportError:
    print "You need PyYaml. Try 'easy_install pyyaml'"
    sys.exit()

try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extensions import register_type, UNICODE, connection
except ImportError:
    print "You need psycopg2 to run this script. Try to install it with 'easy_install psycopg2'"
    sys.exit()

print "Translating... "

class Ddict(dict):
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)

try:
    f = open('translation2js.yaml', 'r')
    yml = f.read()
except:
    print "Critical error: Cannot read config file. Exit"
    sys.exit()
finally:
    f.close()

config = yaml.load(yml)

try:
   conn=psycopg2.connect(config['dsn'])
   print "Database connection established"
except:
   print "Critical Error: Unable to connect to the database. Exit"
   sys.exit()

register_type(UNICODE)
conn.set_client_encoding('UTF8')

# Create a multinensional array [lang][msg-ud]  Example: translationDict["it"]["zoomin"]
translationDict = Ddict(dict)

for lang in config['langs']:

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(config['sql'])

    rows = cur.fetchall()

    for row in rows:
        translationDict[lang][row["msg_id"]] = row[lang]


# Parsing the file empty.js and write msgids into var_arr
try:
    file_emptyjs = open(Path2emptyjs + config["emptyFilename"],'r')
except:
    print "is the path to the directory i18n correct?"
    sys.exit()
var_arr = []
for line in file_emptyjs:
    int_begin = line.find("'") + 1
    int_end = line.rfind("'")
    if (int_begin > 0) and (int_end > 0):
        var_arr.append(line[int_begin:int_end])


# Writing the translated files
for lang in config["langs"]:
    print "Writing: " + lang + ".js"
    print "------------------------"
    try:
        file_langjs = open(Path2emptyjs + lang + '.js','w')
    except:
        print "is the path to the directory i18n correct?"
        sys.exit()

    # Writing header
    file_langjs.write("/*global OpenLayers:true*/\n\n/**\n * @requires OpenLayers/Lang/" + lang + ".js\n */\n\nOpenLayers.Util.extend(OpenLayers.Lang." + lang + ", {\n\n\t//Globals\n")

    int_counter = 1
    var_arr.sort()
    for var_msgid in var_arr:
        if int_counter < len(var_arr):
            try:
                print var_msgid + translationDict[lang][var_msgid]
                file_langjs.write("\t'" + var_msgid + "':\"" + translationDict[lang][var_msgid].replace("'","`") + "\",\n")
            except:
                print var_msgid + " //TODO"
                file_langjs.write("\t'" + var_msgid + "':\"" + var_msgid + "\", //TODO\n")

        # the last entry and footer
        else:
            try:
                print var_msgid + translationDict[lang][var_msgid]
                file_langjs.write("\t'" + var_msgid + "':\"" + translationDict[lang][var_msgid].replace("'","`") + "\n});")
            except:
                print var_msgid + " //TODO"
                file_langjs.write("\t'" + var_msgid + "':\"" + var_msgid + "\" //TODO\n});")


        int_counter += 1

    file_langjs.close()



