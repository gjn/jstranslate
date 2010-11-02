# -*- coding: utf-8 -*- 

import sys, os, subprocess
from mako.template import Template
from mako import exceptions


try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.extensions import register_type, UNICODE, connection
except ImportError:
    print "You need psycopg2 to run this script. Try to install it with 'easy_install psycopg2'"
    sys.exit()

projdir = os.path.abspath(os.path.join('..',os.path.dirname(__file__)))


class Mapfilize():
	
	layers = []
	
	tplvars = None
	
	project = 'wms-bgdi'
	
	project_dir = os.path.abspath(os.path.join(os.curdir,'..','services', project))
	
	def __init__(self):
		self.connect()
		self.initLayers()
		
	def connect(self):
		try:
   			self.conn=psycopg2.connect("dbname='bod' user='www-data' password='www-data' port=5432 host='localhost'")
   			print "Database connection established"
		except:
   			print "Critical Error: Unable to connect to the database. Exit"
   			sys.exit()
	
	def initLayers(self):
		cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        	cur.execute("SELECT fk_id_dataset FROM xt_dataset_wms WHERE fk_map_name LIKE '%wms-bgdi%' ORDER BY 'ch.'||split_part(fk_id_dataset,'.',2)||'.' DESC ,sort_key DESC")

        	for row in  cur.fetchall():
		
			self.layers.append(row['fk_id_dataset'])
		print "Add %d layer(s) to mapfile" % len(self.layers)
		return True
		
	def writeMapfile(self):
		tpl = Template(filename= os.path.join( self.project_dir, self.project +'.map.mako'), input_encoding = 'utf-8')
		self.tplvars = type('tplvars',(object,),{})
		
		self.tplvars.layers = self.layers

		renderedTpl = None
		try:
            		renderedTpl = tpl.render_unicode(c=self.tplvars)
		except:
     			print exceptions.text_error_template().render()
		if renderedTpl is not None:
            		#logging.debug(renderedTpl)
            		filename =  os.path.join( self.project_dir, self.project + '.map')
            		FILE = open(filename,"w")
            		FILE.writelines(renderedTpl.encode('utf-8'))
            		FILE.close()
            		print "Mapfile written successfullyi to %s" %  filename
            		return True
		print "mapfile creation failed!!!"        


if __name__ == '__main__':
    newMapfile = Mapfilize()
    #print newWMS.layers
    newMapfile.writeMapfile()
    


