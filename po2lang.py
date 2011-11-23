#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path, sys, shutil
import re
import gettext, codecs
import subprocess
import version
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



MAXSCALEDENOM = 100000000
MINSCALEDENOM = 0.1
MAX_EXTENT = "100000 50000 850000 400000"

WATERMARK_LAYERNAME = "ch.swisstopo.watermark"
WATERMARK_BGDI_LIST = "ch.bazl.watermark,tutu"


# Full list
WMS_SRS = "EPSG:4326 EPSG:21780 EPSG:21781 EPSG:21782 EPSG:2056 EPSG:4230 EPSG:4258 EPSG:3034 EPSG:3035 EPSG:3043 EPSG:3044 EPSG:25831 EPSG:25832 EPSG:25833 EPSG:2154 EPSG:32631 EPSG:32632 EPSG:4807 EPSG:4275 EPSG:27562 EPSG:27572 EPSG:2192 EPSG:4314 EPSG:31466 EPSG:31467 EPSG:4670 EPSG:3064 EPSG:3065 EPSG:3003 EPSG:3004 EPSG:32631 EPSG:32632 EPSG:23031 EPSG:23032 EPSG:3416 EPSG:31251 EPSG:31254 EPSG:31257 EPSG:4171 EPSG:4151"

WMS_= "EPSG:4979 EPSG:4326 EPSG:900913 EPSG:3857 EPSG:3395 EPSG:32631 EPSG:32632 EPSG:4258 EPSG:4230 EPSG:3035 EPSG:3034 EPSG:3043 EPSG:3044 EPSG:4171 EPSG:4807 EPSG:2154 EPSG:32631 EPSG:32632 EPSG:27572 EPSG:4314 EPSG:31466 EPSG:31467 EPSG:31468 EPSG:31469 EPSG:2398 EPSG:2399 EPSG:25832 EPSG:25833 EPSG:4670 EPSG:3064 EPSG:3065 EPSG:4265 EPSG:3003 EPSG:3004 EPSG:3416 EPSG:31251 EPSG:31254 EPSG:31257 EPSG:31287 EPSG:31297 EPSG:21781 EPSG:21782 EPSG:21780 EPSG:2056 EPSG:4151"

# Trusted ecogis!
WMS_SRS = "EPSG:21781 EPSG:2056 EPSG:4326 EPSG:31466 EPSG:31467 EPSG:31468 EPSG:25832 EPSG:27582 EPSG:26591 EPSG:26592 EPSG:900913"

# Smaller list, for IGN
WMS_SRS = "EPSG:4326 EPSG:21781 EPSG:2056 EPSG:3034 EPSG:3035 EPSG:4258 EPSG:900913"

# Smaller list, but also for D/A/CH/I
WMS_SRS = "EPSG:4326 EPSG:21781 EPSG:2056 EPSG:3034 EPSG:3035 EPSG:4258 EPSG:900913 EPSG:31287 EPSG:25832 EPSG:25833 EPSG:31467 EPSG:32632 EPSG:32633"



localedir = os.path.join( os.path.abspath(os.path.join(os.curdir,'..', "locale")))
langid  = 'de'
domain = 'wms-bod'  # for layers.mo

# OPACITY 100 is default. Do not show in Mapfile.
transparency = opacity = 100



def t(input):
    return _(input)

def iso2utf(s):
      return s.decode('iso-8859-1').encode('utf-8') 

def uni2iso(s):

      return s.encode('iso-8859-1','replace').replace("\"","'")

def xmlnamify(s):
   s = re.sub(r"\[|\]", '', s)
   s = re.sub(r"\(|\)", '', s)
   s = re.sub(r"\"|'", '_', s)
   s = re.sub(r"\s+", '_', s)
   return s


def getSvnVersion(proj_dir):
    p = subprocess.Popen("svnversion %s" %  proj_dir,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    outputlines = p.stdout.readlines()

    return filter(str.isdigit, outputlines[0])


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
        data = unicode(f.read(),'iso-8859-1')
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

def localizeMapfile(project='wms-bod', langs=['fr','de'], projdir = None):
    map = None
    domain = project
    project_dir = os.path.abspath(os.path.join(os.curdir,'..','services', project))
    proj_version = version.get_svn_revision(project_dir)
    print  "Translating", project
    print "===================="
    print "SVN version: ", proj_version
    print "Locales (.mo) are in", localedir

    mapfile_tpl = os.path.join(project_dir, project + '.map')
    
    if os.path.isfile(mapfile_tpl):
        map = mapscript.mapObj(mapfile_tpl)
        print "Using mapfile ", mapfile_tpl
        print "Languages: ", ",".join(langs)

    if map:
        try:
            max_extent = map.getMetaData("wms_extent")
        except:
            max_extent = MAX_EXTENT 
        print "Max extent", max_extent
        for lang in langs:

            try:
               translation = gettext.translation(domain,localedir, languages=[lang])
            except IOError, e:
               print "Error! Cannot initialize translation", e
               print "Try to run bod2po.py first"
               sys.exit()
            translation.install(unicode=1)
            #print translation.info()
            _ = translation.ugettext

            s = 'ch.swisstopo.vec25-heckenbaeume-linien.Hecke.name'
            print "Test translation:", s," --> ",  _(s)
            
            fn = project + '.' + lang + '.yaml'
            #fn = 'wms-bod.' + lang + '.yaml' # for all project
            print "Opening %s (be patient)" % fn
            stream = file(fn , 'r')
            try:
                bodDict =  yaml.load(stream, Loader=Loader)

            except:
                print "Critical error: Cannot read '%s'. Exit" % fn
                sys.exit()
            finally:
                stream.close()




            clone_map = map.clone()
            localized_mapfilename = os.path.abspath(os.path.join(project_dir,project + '.' + lang +'.map'))

            
            # mapfile translation
#            key = clone_map.web.metadata.nextKey(None)
#            while key is not None:
#                value = clone_map.web.metadata.get(key)
#                clone_map.web.metadata.set(key, value ) #uni2iso(value))
#                key = clone_map.web.metadata.nextKey(key)
                
            # clone_map.web.metadata.set('wms_abstract', uni2iso(_('wms-bod.wms_abstract')))
            clone_map.web.metadata.set('wms_abstract', uni2iso(_( project +'.wms_abstract') + " (Revision: %s)" % proj_version))
            clone_map.web.metadata.set('wms_encoding', bodDict['wms'][project]['encoding'])
            clone_map.web.metadata.set('wms_contactorganization', uni2iso(_(project + '.wms_contactorganization')))
            clone_map.web.metadata.set('wms_title', uni2iso(_(project + '.wms_title')))
            clone_map.web.metadata.set('ows_enable_request', '*')
            clone_map.defresolution = clone_map.resolution
            if project == 'wms-bgdi':
                clone_map.web.metadata.set('wms_srs', WMS_SRS)

            for i in range(0, clone_map.numlayers):
                lyr = clone_map.getLayer(i)
                if lyr:
                    # Layer stuff and fixing
                    if lyr.name == WATERMARK_LAYERNAME or project != 'wms-bod' :
                        opacity = transparency = lyr.opacity
                    else:
                        opacity = transparency = 100
                        
                    lyr.opacity = opacity
                    lyr.transparency = transparency
                    # No template (not queryable by default) 
                    lyr.template = 'ttt' # How do we know if it is queryable None

                    if lyr.name in bodDict['layers'].keys():
                        gml_include_items = bodDict['layers'][lyr.name]['gml_include_items']
                        if gml_include_items:
                             lyr.metadata.set('gml_include_items', gml_include_items)
                             #item value contains sometime invalid character
                             lyr.metadata.set('wms_include_items', gml_include_items)
                             # Queryable
                             lyr.template = 'GetFeatureInfo'
    
                        setScale(lyr, key='minscaledenom',value= bodDict['layers'][lyr.name]['ms_minscaledenom'])
                        setScale(lyr, key='maxscaledenom',value= bodDict['layers'][lyr.name]['ms_maxscaledenom'])

                        group_id  = bodDict['layers'][lyr.name]['group_id']
                        if group_id:
                            lyr.group = group_id
                            lyr.metadata.set('wms_group_title', uni2iso(_(lyr.name+'.wms_group_title')).replace("'","`"))
                            lyr.metadata.set('wms_group_abstract', uni2iso(_(lyr.name+'.wms_group_abstract')).replace("'","`"))

                            
                            
                        else:
                              lyr.group = None
                              if lyr.metadata.get('wms_group_title'):
                                lyr.metadata.remove('wms_group_title')

                        lyr.metadata.set('dump_source', bodDict['layers'][lyr.name]['datasource'] )
                    # Status
                    lyr.status = mapscript.MS_OFF
                   
                    if lyr.name in WATERMARK_BGDI_LIST.split(",") :
                        lyr.status=mapscript.MS_DEFAULT
 
                    extent = lyr.metadata.get("wms_extent")
                    if not extent:
                        lyr.metadata.set("wms_extent", max_extent)


                    if project == 'wms-bod':
                        # layer translation, if group take title and absctract from group
                        if lyr.group and _(lyr.name+'.wms_title') == lyr.name+'.wms_title':
                            lyr.metadata.set('wms_title',uni2iso(_(lyr.name+'.wms_group_title')))
                        else:
                            lyr.metadata.set('wms_title', uni2iso(_(lyr.name+'.wms_title')))
                        #print _(u''+lyr.name+'.title')

                        if lyr.group and _(lyr.name+'.wms_abstract') == lyr.name+'.wms_abstract':
                            lyr.metadata.set('wms_abstract',uni2iso(_(lyr.name+'.wms_group_abstract')))
                        else:
                            lyr.metadata.set('wms_abstract', uni2iso(_(lyr.name+'.wms_abstract')))
                        # No labels
                        lyr.labelmaxscaledenom = 2.0
                        lyr.labelminscaledenom = 1.0
                    else:
                        lyr.metadata.set('wms_title', uni2iso(_(lyr.name+'.wms_title')).replace("'","`"))
                        lyr.metadata.set('wms_abstract', uni2iso(_(lyr.name+'.wms_abstract')).replace("'","`"))
                        lyr.metadata.set('wms_srs', WMS_SRS)
                        maxscaledenom = lyr.maxscaledenom
                        if maxscaledenom < 0:
                            lyr.maxscaledenom = MAXSCALEDENOM
                        minscaledenom = lyr.minscaledenom
                        if minscaledenom < 0:
                            lyr.minscaledenom = MINSCALEDENOM

                    # print  t(lyr.name+'.title')
                    # print _(lyr.name+'.abstract')


                    items = lyr.metadata.get("gml_include_items")
                    if items:
                        for item in items.split(','):
                            item = item.strip()
                            gml_item_alias = "gml_%s_alias" % item
                            wms_item_alias = "wms_%s_alias" % item
                            item_translation = uni2iso(_(lyr.name+'.'+item+'.name'))
                            lyr.metadata.set(gml_item_alias, xmlnamify(item_translation))
                            lyr.metadata.set(wms_item_alias, xmlnamify(item_translation))
                    # Classes stuff and fixing
                    for j in range(0, lyr.numclasses):
                        klass = lyr.getClass(j)
                        if klass and klass.name:
                            # Fix scales
                            klassid = lyr.name + "." + klass.name.decode('utf-8','replace')
                            if klassid in bodDict['classes'].keys():
                                setScale(klass, key='minscaledenom',value= bodDict['classes'][klassid]['ms_minscaledenom'])
                                setScale(klass, key='maxscaledenom',value= bodDict['classes'][klassid]['ms_maxscaledenom'])


                            klass.opacity = opacity
                            klass.transparency = transparency

                            #klassname = lyr.name + "." + klass.name.decode('utf-8','replace') + ".name"
                            # ch.swisstopo.vec200-names-namedlocation.Tunnel.name
                            # ch.swisstopo.vec25-heckenbaeume-linien.Hecke.name
                            # klassid=ch.swisstopo.vec25-heckenbaeume_linien.Hecke, klass.name=Hecke

                            #print "klassid=%s, klass.name=%s" % (klassid,klass.name)
                            klassname = klassid + ".name"
                            print klassname
                            #print "CLASS, id=%s" % klassname
                            klass.name =uni2iso( _(klassname))  #.encode('ascii','replace')))
                            #if klassname == klass.name:
                            #   print "Missing translation for", klassname
                            

           
            if os.path.exists(localized_mapfilename):
                value = raw_input("Overwrite %s ? [y,n]" % localized_mapfilename)
                if value.strip() in ['y','Y','o','O']:
                    clone_map.save(localized_mapfilename)
            else:
                 clone_map.save(localized_mapfilename)
                 
            
      
            s = iso2utf(open(localized_mapfilename).read())

            # wms-swistopowms: remove _tilecache
            if project == 'wms-swisstopowms':
            	s = s.replace("_tilecache", "") 
        
            open(localized_mapfilename, 'w').write(s)
            #convert_to_utf8(localized_mapfilename)

    else:
        print "Error opening", mapfile_tpl
                

if __name__ == '__main__':
   if not sys.argv[1:]:
       sys.stdout.write("Sorry, you must specify one argument, for instance wms-bod")
       sys.exit(0)
   else:
      localizeMapfile(sys.argv[1])

