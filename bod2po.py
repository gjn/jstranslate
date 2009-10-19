#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-*- encoding: utf8 -*-

import os, sys, subprocess

try:
    import yaml
except ImportError:
    print "You need PyYaml. Try 'easy_install pyyaml'"
    sys.exit()

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extensions import register_type, UNICODE, connection
except ImportError:
    print "You need psycopg2 to run this script. Try to install it with 'easy_install psycopg2'"
    sys.exit()

try:
    from babel.messages import Catalog, pofile
except ImportError:
    print "You need babel to run this script. Try to install it with 'easy_install babel'"
    sys.exit()

project = 'wms-bod'

projdir = os.path.abspath(os.path.join('..',os.path.dirname(__file__)))
podir = os.path.join(projdir,'po')




if not os.path.exists(podir):
        os.makedirs(podir)

try:
    f = open('bod2po.yaml', 'r')
    yml = f.read()
except:
    print "Critical error: Cannot read config file. Exit"
    sys.exit()
finally:
    f.close()

config = yaml.load(yml)

def trim(str):
    if str:
        return str.strip()
    else:
        return str

print config['dsn']
try:
   conn=psycopg2.connect(config['dsn'])
   print "Database connection established"
except:
   print "Critical Error: Unable to connect to the database. Exit"
   sys.exit()

register_type(UNICODE)
conn.set_client_encoding('UTF8')



for lang in config['langs']:
    catalog = Catalog(project=project, locale=lang)
    for proj in config['tables']:
        print "Table: ", proj
        print "---------------------"
        field_id = config['tables'][proj]['id']
        pg_table = config['tables'][proj]['table']
        

        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(config['tables'][proj]['sql'])

        rows = cur.fetchall()
        for row in rows:
            for field in config['tables'][proj]['fields']:
                field_name = field + '_' + lang
                field_value = row[field_name]
                id = row[field_id]
                print "Adding", id
                raw_string = trim(field_value)
                if raw_string:
                    try:
                        cleaned_string = raw_string.encode('iso-8859-1').decode('iso-8859-1')
                    except UnicodeEncodeError:
                        msg = u"Error!\nThe string \"%s\" contains illegal character(s).\nPlease check the table \"%s\" and correct id=%s (illegal character(s) replaced by '?').\nExit" % (raw_string,pg_table,id)
                        print msg.encode('iso-8859-1','replace')
                        sys.exit()

                    catalog.add(trim(u"%s.%s" % (id, config['tables'][proj][field])), string = cleaned_string)
    
    po_filename = os.path.join(podir,"%s.%s.po"  % (project,lang))
    print po_filename        

    try:
             
            
            po = open(po_filename,'w')
            pofile.write_po(po, catalog, omit_header=False)

    finally:
            po.close()

    locale_dir = os.path.join(projdir,"locale",lang, "LC_MESSAGES")
    mofile = "%s/%s.mo" % (locale_dir, project)

    if not os.path.exists(locale_dir):
        os.makedirs(locale_dir)
   
    p = subprocess.Popen(["msgfmt",'-o',mofile, po_filename],stdout=subprocess.PIPE);
    print p.communicate()[0]
 
    print "bod2po.py successfully terminated."

