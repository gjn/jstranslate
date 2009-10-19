#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path, sys
import gettext

try:
    import mapscript
except ImportError:
    print "Critical error. Import module 'mapscript' failed. Exit"
    sys.exit()




localedir = os.path.join( os.path.abspath(os.path.join(os.curdir,'..', "locale")))
langid  = 'de'
domain = 'wms-bod'  # for layers.mo

print localedir

def t(input):
    return _(input)

def iso2utf(s):
      return s.decode('iso-8859-1').encode('utf-8') 

def uni2iso(s):
      return s.encode('iso-8859-1','replace') 

def localizeMapfile(project, langs=['fr','de'], projdir = None):
    map = None
    project_dir = os.path.abspath(os.path.join(os.curdir,'..','services', project))
    mapfile_tpl = os.path.join(project_dir, project + '.map')
    if os.path.isfile(mapfile_tpl):
        map = mapscript.mapObj(mapfile_tpl)
    if map:
        for lang in langs:

            translation = gettext.translation(domain,localedir, languages=[lang])
            translation.install(unicode=1)
            #print translation.info()
            _ = translation.ugettext


            print _("ch.swisstopo.gg25-gemeinde-grenze.title")



            clone_map = map.clone()
            localized_mapfilename = os.path.abspath(os.path.join(project_dir,project + '.' + lang +'.map'))

            


            for i in range(0, clone_map.numlayers - 1):
                lyr = clone_map.getLayer(i)
                if lyr:
                    lyr.metadata.set('wms_title', uni2iso(_(lyr.name+'.wms_title')))
                    #print _(u''+lyr.name+'.title')
                    print  t(lyr.name+'.title')
                    lyr.metadata.set('wms_abstract', uni2iso(_(lyr.name+'.wms_abstract')))
                    print _(lyr.name+'.abstract')


                    items = lyr.metadata.get("gml_include_items")
                    if items:
                        for item in items.split(','):
                            item = item.strip()
                            item_alias = "gml_%s_alias" % item
                            item_translation = uni2iso(_(lyr.name+'.'+item+'.name'))
                            lyr.metadata.set(item_alias, item_translation)

                    
                    for j in range(0, lyr.numclasses):
                        klass = lyr.getClass(j)
                        if klass and klass.name:
                            #klassname = lyr.name + "." + klass.name.decode('utf-8','replace') + ".name"
                            klassname = lyr.name + "." + klass.name.decode('utf-8','replace') + ".name"

                            print "CLASS,",  klassname.encode('ascii','replace')
                            klass.name =uni2iso( _(klassname))  #.encode('ascii','replace')))
                            
                            

           
            if os.path.exists(localized_mapfilename):
                value = raw_input("Overwrite %s ? [y,n]" % localized_mapfilename)
                if value.strip() in ['y','Y','o','O']:
                    clone_map.save(localized_mapfilename)
            else:
                 clone_map.save(localized_mapfilename)
                 
            
      
            s = iso2utf(open(localized_mapfilename).read())
            open(localized_mapfilename, 'w').write(s)
    else:
        print "Error opening", mapfile_tpl
                

if __name__ == '__main__':
   localizeMapfile('wms-bod')

