#!/usr/bin/env python
'''
Uninstall DocDB
'''

import os,re
import json
def alter(file,old_str,new_str):
  with open(file, "r") as f1,open("%s.bak" % file, "w") as f2:
    for line in f1:
      f2.write(re.sub(old_str,new_str,line))
  os.remove(file)
  os.rename("%s.bak" % file, file)

json_path="installation.json"
if(os.path.exists(json_path)):
  install_data=json.load(open(json_path))
  db_name=install_data['db_name']
  db_admuser=install_data['db_admuser']
  db_rwuser=install_data['db_rwuser']
  db_rouser=install_data['db_rouser']

  os.system("rm -rf "+install_data['root_path'])
  os.system("rm -rf "+install_data['web_conf'])
  os.system("rm -rf "+install_data['web_access_log'])
  os.system("rm -rf "+install_data['web_error_log'])

  os.system("cp drop_db.sql.template drop_db.sql")
  os.system("cp delete_user.sql.template delete_user.sql")
  alter("drop_db.sql", "{db_name}", db_name)
  alter("delete_user.sql", "{db_admuser}", db_admuser)
  alter("delete_user.sql", "{db_rwuser}", db_rwuser)
  alter("delete_user.sql", "{db_rouser}", db_rouser)
  
  #str="mysql -uroot -p"+install_data['db_root_pass']+" < drop_db.sql"
  #print(str)
  
  os.system("mysql -uroot -p"+install_data['db_root_pass']+" < drop_db.sql")
  os.system("mysql -uroot -p"+install_data['db_root_pass']+" < delete_user.sql")

  os.remove("drop_db.sql")
  os.remove("delete_user.sql")

  print("Your Project '"+install_data['project_name']+" Document Databse' has been removed!" )
  print("Welcome to use next time!" )
  #os.remove(json_path)
else:
  print("Your 'installation.json' file dosen't exist!" )
