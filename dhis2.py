from functools import lru_cache
import json
import pickle
from pathlib import Path
import urllib

import requests
ses = requests.Session() # create and cache single session for entire script run

API_PATH = 'api/' #'api/29/'

from district_regions import *

INDICATOR_ALIASES = dict()
AGE_GROUP_ALIASES = dict()
ORGUNIT_ALIASES = dict()

class DataElement(object):
    def __init__(self, obj_tree):
        self.obj_tree = obj_tree
    
    def __getitem__(self, key):
        if key in self.obj_tree:
            return self.obj_tree[key]
        else:
            raise KeyError(key)

    @lru_cache()
    def find_category_combo(self, *args):
        for coc in self.obj_tree['categoryCombo']['categoryOptionCombos']:
            if all([any([co['name'] == x or co['id'] == x or co['name'] == AGE_GROUP_ALIASES.get(x) or co['id'] == AGE_GROUP_ALIASES.get(x) for x in args]) for co in coc['categoryOptions']]):
                return (coc['id'], coc['name'])
        return None
    
    def __str__(self):
        return str(self.obj_tree)

class OrgUnit(object):
    def __init__(self, obj_tree, orgunits):
        self.obj_tree = obj_tree
        self.orgunits = orgunits
        self.attribs = dict()
        self.groups = list()
        for ou_g in self.obj_tree['organisationUnitGroups']:
            if 'groupSets' in ou_g:
                if len(ou_g['groupSets']) > 0:
                    g_set = ou_g['groupSets'][0]
                    g_set_name = self.orgunits.OU_GROUP_SET_MAP[g_set['id']]
                    self.attribs[g_set_name] = ou_g['name']
            else:
                self.groups.append(ou_g['name'])
    
    def __getitem__(self, key):
        if key in self.obj_tree:
            return self.obj_tree[key]
        elif key in self.attribs:
            return self.attribs[key]
        else:
            raise KeyError(key)

    def get(self, *args, **kwargs):
        return self.obj_tree.get(*args, **kwargs)
    
    def ancestor_path(self):
        return tuple(self.orgunits[p['id']]['name'] for p in self.obj_tree['ancestors'])
    
    def __str__(self):
        non_attribs = { k:v for k,v in self.obj_tree.items() if k not in ('dataSets', 'organisationUnitGroups') }
        non_attribs['organisationUnitGroups'] = self.groups
        # return str({ **non_attribs, **self.attribs })
        return json.dumps({ **non_attribs, **self.attribs })

class OrgUnits(object):
    def __init__(self, server_instance):
        self.server_instance = server_instance

        params = { 'fields': 'id,name,code,parent,ancestors,geometry,organisationUnitGroups[id,name,groupSets]', 'paging': 'false' }
        res = server_instance.api_get(API_PATH + 'organisationUnits.json', params)
        self.__ou_cache = res.json()['organisationUnits']
        self.__name_map = dict()
        self.__id_map = dict()

        for ou in self.__ou_cache:
            self.__id_map[ou['id']] = ou
            self.__name_map[ou['name']] = ou

        # OU_GROUP_SET_MAP
        params = { 'fields': 'id,name,organisationUnitGroups[id,name]', 'paging': 'false' }
        res = server_instance.api_get(API_PATH + 'organisationUnitGroupSets.json', params)
        self.OU_GROUP_SET_MAP = { ou_gs['id']:ou_gs['name'] for ou_gs in res.json()['organisationUnitGroupSets'] }
    
    def __getitem__(self, key):
        if isinstance(key, int):
            obj_tree = self.__ou_cache[key]
        else:
            obj_tree = self.__id_map[key]
        return OrgUnit(obj_tree, self)

    def lookup_name(self, ou_name):
        alias = ORGUNIT_ALIASES.get(ou_name)
        if alias:
            alias_match = self.__name_map.get(alias)
            if alias_match:
                return OrgUnit(alias_match, self)

        ou_objtree = self.__name_map.get(ou_name, None)
        if ou_objtree is None:
            raise KeyError(f'No Organisation Unit with the name "{ou_name}" found in DHIS2 instance "{self.server_instance.server_url}"')

        return OrgUnit(ou_objtree, self)

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.__id_map
            
        return false

    def __iter__(self):
        return (OrgUnit(ou, self) for ou in self.__ou_cache)

    def __len__(self):
        return len(self.__ou_cache)
    
    def ancestor_path(self, ou_name):
        return tuple(self[p['id']]['name'] for p in self.lookup_name(ou_name)['ancestors'])

    def __str__(self):
        return 'server_url: %s, size: %d' % (self.server_instance.server_url, len(self.__ou_cache))

class DataSets(object):
    def __init__(self, server_instance):
        self.server_instance = server_instance

        params = { 'fields':'id,name,dataSetElements', 'paging': 'false' }
        res = server_instance.api_get(API_PATH + 'dataSets.json', params)
        self.__ds_cache = res.json()['dataSets']
        self.__name_map = dict()
        self.__id_map = dict()

        for ds in self.__ds_cache:
            self.__id_map[ds['id']] = ds
            self.__name_map[ds['name']] = ds
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.__ds_cache[key]
        else:
            return self.__id_map[key]

    def lookup_name(self, ds_name):
        return self.__name_map[ds_name]

    def __str__(self):
        return 'server_url: %s, size: %d' % (self.server_instance.server_url, len(self.__ds_cache))

import re
escape_sequence = re.compile(r'\\x([a-zA-Z0-9]{2})')
def repair(string):
    return escape_sequence.sub(r'\\u00\1', string)
    #just use json.loads(repair(line))

class DataElements(object):
    def __init__(self, server_instance):
        self.server_instance = server_instance

        params = { 'fields':'id,name,categoryCombo[id,name,categoryOptionCombos[id,name,categoryOptions[id,name]]]', 'paging': 'false' }
        res = server_instance.api_get(API_PATH + 'dataElements.json', params)
        self.__de_cache = res.json()['dataElements']
        self.__name_map = dict()
        self.__id_map = dict()

        for de in self.__de_cache:
            self.__id_map[de['id']] = de
            self.__name_map[de['name']] = de
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.__de_cache[key]
        else:
            return self.__id_map[key]

    def lookup_name(self, de_name):
        alias = INDICATOR_ALIASES.get(de_name)
        if alias:
            obj_tree = self.__name_map.get(alias)
        else:
            obj_tree = self.__name_map.get(de_name)
        if obj_tree:
            return DataElement(obj_tree)
        else:
            return None

    def __str__(self):
        return 'server_url: %s, size: %d' % (self.server_instance.server_url, len(self.__de_cache))

from functools import wraps
from time import time

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('func:%r args:[%r, %r] took: %2.4f sec' % (f.__name__, args, kw, te-ts))
        return result
    return wrap

class Dhis2(object):
    def __init__(self, server_url, credentials, cache_dir=None):
        self.server_url = server_url
        self.credentials = credentials
        self.cache_dir = cache_dir

    def api_get(self, path, query_params):
        req_url = urllib.parse.urljoin(self.server_url, path)
        r = ses.get(req_url, params=query_params, auth=self.credentials)
        r.raise_for_status() # throw exception if there is a problem
        return r

    def api_post(self, path, query_params=None, custom_headers=None, post_data=None):
        req_url = urllib.parse.urljoin(self.server_url, path)
        r = ses.post(req_url, params=query_params, auth=self.credentials, headers=custom_headers, data=post_data)
        r.raise_for_status() # throw exception if there is a problem
        return r

    @timing
    def orgunits(self):
        if self.cache_dir:
            if Path(self.cache_dir / 'orgunits.pickle').exists():
                with open(self.cache_dir / 'orgunits.pickle', mode='rb') as pkf:
                    return pickle.load(pkf)
            else:
                orgunits = OrgUnits(self)
                with open(self.cache_dir / 'orgunits.pickle', mode='wb') as pkf:
                    pickle.dump(orgunits, pkf)
        else:
            orgunits = OrgUnits(self)
        return orgunits
    def datasets(self):
        return DataSets(self)
    @timing
    def dataelements(self):
        return DataElements(self)

    def __str__(self):
        return "Dhis2(u'%s', ('%s', 'XXXXXX'))" % (str(self.server_url), str(self.credentials[0]))

def load_mappings(mappings_dir_path):
    # Load organisation unit mappings
    with open(mappings_dir_path / 'orgunits.json') as file_ou:
        dict_ou = dict(json.load(file_ou))
        ORGUNIT_ALIASES.update(dict_ou)

if __name__ == "__main__":
    import argparse
    import sys
    import csv
    from pathlib import Path
    import datetime

    from hmis_health_go_ug import DHIS2_SERVER_URL
    from hmis_health_go_ug import credentials
    #from hmis_nacop_net import DHIS2_SERVER_URL
    #from hmis_nacop_net import credentials
    # DHIS2_SERVER_URL = 'https://play.dhis2.org/2.31.8/'
    # credentials = ('admin', 'district')

    parser = argparse.ArgumentParser(prog='json2dxfdict')
    parser.add_argument('--cached', action='store_true', default=False, help='Load metadata from cache')
    parser.add_argument('--metadata', action='store_true', default=False, help='Stop processing after loading metadata')
    parser.add_argument('--limit', type=int, default=-1, help='Only process LIMIT entries')
    args = parser.parse_args()

    base_path, *_ = [p for p in Path(__file__).resolve().parents if p.is_dir()] # extra complications in case we are in a zip archive module

    if args.cached:
        dhis2_inst = Dhis2(DHIS2_SERVER_URL, credentials, base_path)
    else:
        dhis2_inst = Dhis2(DHIS2_SERVER_URL, credentials)

    load_mappings(base_path)

    # Load DHIS2 metadata
        # datasets = DataSets(DHIS2_SERVER_URL)
        # print(datasets)
        # dataelements = dhis2_inst.dataelements()
        # print(dataelements)

    orgunits = dhis2_inst.orgunits()

    kisiizi = orgunits.lookup_name('Cou Kisiizi Hospital')

    if args.metadata:
        sys.exit()

    OUTPUT_FILE = 'UG_MFL_%s.csv' % (datetime.date.today().isoformat(),)

    with open(base_path / OUTPUT_FILE, mode='w') as csvfile:
        csvwriter = csv.writer(csvfile, quoting=csv.QUOTE_ALL, lineterminator='\n')
        csvwriter.writerow(("REGION","SUB_REGION","DISTRICT","SUBCOUNTY","NAME","UID","COORDINATES","OPERATIONAL STATUS", "FACILITY_LEVEL","OWNERSHIP_NAME","AUTHORITY_NAME"))

        for i, ou_tree in enumerate(orgunits):
            ou = OrgUnit(ou_tree, orgunits)
            ou_name, ou_id, ou_geometry = [ou.get(x, '') for x in ('name', 'id', 'geometry')]
            ou_path = ou.ancestor_path() + (ou_name,)
            if len(ou_path) > 1:
                # add the missing 'REGION' section of the 
                ou_path = ou_path[:1] + (SUBREGION_REGION[ou_path[1]], ) + ou_path[1:]
            if len(ou_path) < 6:
                ou_path = ou_path + ('',) * (6 - len(ou_path)) # pad out short orgunit paths
            ou_path = ou_path[1:]
            ou_attribs = [ou.attribs.get(x, '') for x in ('Operational Status', 'Facility Level', 'Ownership', 'Authority')]
            csvwriter.writerow((*ou_path, ou_id, json.dumps(ou_geometry), *ou_attribs))

            if args.limit > 0 and i >= args.limit:
                break
