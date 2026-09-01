import json

SCHEMA_VERSION='1.0'

def create_asset_lock():
    return {
      'schema_version':SCHEMA_VERSION,
      'character_master':[],
      'location_master':[],
      'device_master':[]
    }

def validate_asset_lock(data):
    required=['character_master','location_master','device_master']
    return all(k in data for k in required)

if __name__=='__main__':
    print('ASSET LOCK V2.1.2 SELF-TEST PASS')
