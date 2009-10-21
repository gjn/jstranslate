#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path, sys, shutil
import gettext, codecs

try:
    import mapscript
except ImportError:
    print "Critical error. Import module 'mapscript' failed. Exit"
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


MAXSCALEDENOM = 10000000
MINSCALEDENOM = 1

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


def setScale(object, key='minscaledenom',value=None):
    """ si value > 0 --> replace
        si  value est None --> rien
        si value <0 --> effacer la valeur du mapfile
    """
    if value is None: return

    if value > 0:
        setattr(object,key, int(value))
    else:
        if key =='maxscaledenom':
            setattr(object,key, MAXSCALEDENOM)
        else:
            setattr(object,key, MINSCALEDENOM)


def convert_to_utf8(filename):
    try:
        f = open(filename,'r')
        data = uniocde(f.read(),'iso-8859-1')
    except Exception:
        sys.exit(1)


    newfilename = filename + '.bak'

    shutil.copy(filename,newfilename)

    f = open(filename,'w')
    try:
        data = "# Automatically generated mapfile. Do not edit!\n\n" + data
        #f.write(data.encode('utf-8'))
        f.write(data.encode('utf-8'))

    except Exception, e:
        print e
    finally:
        f.close()

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

            fn = 'wms-bod.' + lang + '.yaml'
            print "Opening ", fn
            stream = file(fn , 'r')
            try:
                bodDict =  yaml.load(stream, Loader=Loader)

            except:
                print "Critical error: Cannot read '%s'. Exit" % fn
                sys.exit()
            finally:
                stream.close()


            print _("ch.swisstopo.gg25-gemeinde-grenze.title")



            clone_map = map.clone()
            localized_mapfilename = os.path.abspath(os.path.join(project_dir,project + '.' + lang +'.map'))

            
            # mapfile translation
            clone_map.web.metadata.set('wms_title', uni2iso(_('wms-bod.wms_title')))
            clone_map.web.metadata.set('wms_abstract', uni2iso(_('wms-bod.wms_abstract')))
            clone_map.web.metadata.set('wms_encoding', bodDict['wms'][project]['encoding'])


            for i in range(0, clone_map.numlayers - 1):
                lyr = clone_map.getLayer(i)
                if lyr:
                    # Layer fixing
                    if lyr.name in bodDict['layers'].keys():
                        gml_include_items = bodDict['layers'][lyr.name]['gml_include_items']
                        if gml_include_items:
                            lyr.metadata.set('gml_include_items', gml_include_items)
                        
                        setScale(lyr, key='minscaledenom',value= bodDict['layers'][lyr.name]['ms_minscaledenom'])
                        setScale(lyr, key='maxscaledenom',value= bodDict['layers'][lyr.name]['ms_maxscaledenom'])

                        group_id  = bodDict['layers'][lyr.name]['group_id']
                        if group_id:
                            lyr.group = group_id
                            lyr.metadata.set('wms_group_title', uni2iso(_(lyr.name+'.wms_group_title')))
                        else:
                              lyr.group = None
                              if lyr.metadata.get('wms_group_title'):
                                lyr.metadata.remove('wms_group_title')

                        lyr.metadata.set('dump_source', bodDict['layers'][lyr.name]['fk_datasource_id'] )




                    # layer translation
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
                            # Fix scales
                            klassid = lyr.name + "." + klass.name.decode('utf-8','replace')
                            if klassid in bodDict['classes'].keys():
                                setScale(lyr, key='minscaledenom',value= bodDict['classes'][klassid]['ms_minscaledenom'])
                                setScale(lyr, key='maxscaledenom',value= bodDict['classes'][klassid]['ms_maxscaledenom'])




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
            #convert_to_utf8(localized_mapfilename)

    else:
        print "Error opening", mapfile_tpl
                

if __name__ == '__main__':
   localizeMapfile('wms-bod')

