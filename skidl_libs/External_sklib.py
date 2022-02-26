from skidl import Pin, Part, Alias, SchLib, SKIDL, TEMPLATE

SKIDL_lib_version = '0.0.1'

_home_dror_src_electronics_skidl_projects_simple_skidl_parts_skidl_libs_External = SchLib(tool=SKIDL).add_parts(*[
        Part(**{ 'name':'TPS54331', 'dest':TEMPLATE, 'tool':SKIDL, 'description':'28-V, 3-A non-synchronous buck converter', '_match_pin_regex':False, 'ref_prefix':'U', 'num_units':None, 'fplist':None, 'do_erc':True, 'aliases':Alias(), 'pin':None, 'footprint':None, 'pins':[
            Pin(num=1,name='BOOT',func=Pin.types.INPUT,do_erc=True),
            Pin(num=2,name='VIN',func=Pin.types.PWRIN,do_erc=True),
            Pin(num=3,name='EN',func=Pin.types.INPUT,do_erc=True),
            Pin(num=4,name='SS',func=Pin.types.INPUT,do_erc=True),
            Pin(num=5,name='VSNS',func=Pin.types.INPUT,do_erc=True),
            Pin(num=6,name='COMP',func=Pin.types.INPUT,do_erc=True),
            Pin(num=7,name='GND',func=Pin.types.PWRIN,do_erc=True),
            Pin(num=8,name='PH',func=Pin.types.PWROUT,do_erc=True)] })])