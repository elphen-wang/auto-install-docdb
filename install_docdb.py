#!/usr/bin/env python
'''
Install DocDB
'''

import os
import json
from subprocess import check_output, check_call

os.environ.setdefault('DOCDB_ROOT','/var/lib/docdb')#/var/www/html
canonical_config_filename = 'installation.json'

thisdir=os.path.dirname(os.path.realpath(__file__))

def pwgen(): 
    return check_output('pwgen -s 12 1',shell=True).strip()

def env(name, default=''):
    var='DOCDB_'+name.upper()
    ret = os.environ.get(var,default)
    #print ('name="%s" var="%s" default="%s" ret="%s"' % (name,var,default,ret))
    return ret

# todo: persist auth tokens

class Config(object):

    defaults = dict(
        root_path = env('root'),#modified
        
        db_name = env('db_name','DocDB'),
        db_host = env('db_host','localhost'),
        db_root_pass = env('db_root_pass',''),

        db_admuser = env('db_admuser','docdbadm'),
        db_admpass = env('db_admpass', pwgen()),
        db_rwuser = env('db_rwuser','docdbrw'),
        db_rwpass = env('db_rwpass', pwgen()),
        db_rouser = env('db_rouser','docdbro'),
        db_ropass = env('db_ropass', pwgen()),

        web_admuser = env('web_admuser', 'docdbadm'),
        web_admpass = env('web_admpass', pwgen()),
        web_rwuser = env('web_rwuser', 'docdbrw'),
        web_rwpass = env('web_rwpass', pwgen()),
        
        # the file system path for the document store
        file_root = env('file_root', os.path.join(env('root'), 'htdocs')),
        # the file system path for the cgi-bin area
        script_root = env('script_root', os.path.join(env('root'), 'cgi-bin')),
        # the FQDN for the web sever
        web_host = env('web_host', 'localhost'),
        # Relative base path part of the URL to locate non-CGI files
        web_base = env('web_base', 'DocDB'),
        # Relative base path part of the URL to locate CGI files ("/private" will go under it),now is /{web_root}
        cgi_base = env('cgi_base', 'cgi-bin'),

        admin_email = env('admin_email','root@localhost'),
        admin_name = env('admin_name','Document Database Administrators'),
        auth_file = env('auth_file', os.path.join(env('root'), 'passwords/htpasswd')),
        smtp_server = env('smtp_server','localhost'),
        first_year = env('first_year', 2000),
        project_name = env('project_name', 'Document Database'),
        project_nick = env('project_nick', 'DocDB'),
        
        ##### new add ####
        web_root = env('web_root', 'private'),#''
        web_port = env('web_port', '8888'),
        web_conf = env('web_conf', '/etc/httpd/conf.d/'+env('project_name', 'Document Database')+'.conf'),
        web_access_log = env('web_access_log', '/var/log/httpd/'+env('web_host', 'localhost')),
        web_error_log = env('web_error_log', '/var/log/httpd/'+env('web_host', 'localhost')+'-error'),
        web_apache_user = env('web_apache_user', 'apache'),
        web_apache_group = env('web_apache_group', 'apache'),
        #db_rootpass = env('db_rootpass', 'root1234'),
        ##################

        giturl = env('giturl','https://gitee.com/hk_donquixote/DocDB_01.git'),
        #https://github.com/brettviren/DocDB.git,
        #https://github.com/ericvaandering/DocDB.git,
        #https://gitee.com/hk_donquixote/DocDB.git
        gittag = env('gittag'),
        srcdir = env('srcdir', os.path.join(env('root'), 'src')),
        my_cnf = env('my_cnf', os.path.join(env('root'), 'my.cnf')),
    )

    def __init__(self, filename=None, **kwds):
        '''Make a config object.  

        If no filename is given the self.defaults is used which may be
        overridden by environment variables.  Environment variables
        take the form of 'DOCDB_<NAME>' where <NAME> is the uppercased
        version of a configuration parameter

        If filename is given it is read as JSON to provide the
        configuration dictionary and self.defaults are ignored.  See
        the .save() method.

        If filename is given as "*canonical*" a canonical location is
        checked (in same directory as this script) and used if found,
        otherwise fallback to self.defaults.

        '''

        # tortured configuration source policy....
        if filename:
            if filename == '*canonical*':
                filename = os.path.join(thisdir, canonical_config_filename)
                if os.path.exists(filename):
                    print ('Reading from canonical: %s' % filename)
                    self._cfg = json.loads(open(filename).read())
                else:
                    print ('No canonical file: %s' % filename)
                    self._cfg = dict(self.defaults)

            elif os.path.exists(filename):
                print ('Using previous configuration from %s' % filename)
                self._cfg = json.loads(open(filename).read())
            else:
                raise RuntimeError('No such file: %s' % filename)
        else:
            print ('Using default/environment configuration')
            self._cfg = dict(self.defaults)

        self._cfg.update(kwds)
            
    def __getattr__(self, name):
        return self._cfg[name]

    def format(self, string, **kwds):
        dat = dict(self._cfg)
        dat.update(kwds)
        return string.format(**dat)

    def asdict(self):
        return dict(self._cfg)

    def save(self, filename):
        '''Save this configuration to filename.

        If filename already exists it will first be moved to new name
        with .old extension.

        If filename is *canonical* or None the canonical location will
        be used (same directory as holding this script)
        '''
        if filename is None or filename == "*canonical*":
            filename = os.path.join(thisdir, canonical_config_filename)

        if os.path.exists(filename):
            last = json.load(open(filename))
            if last == self.asdict():
                return filename
            os.rename(filename, filename+'.old')
        open(filename,'w').write(json.dumps(self.asdict(), indent=2,sort_keys=True))#new add sort
        return filename

class Install(object):

    def __init__(self, cfg):
        self.cfg = cfg

    def __call__(self):
        self.install_docdb_files()
        self.configure_mysql()

    def info(self, string, **kwds):
        print (self.cfg.format('Info: ' + string, **kwds))

    def warn(self, string, **kwds):
        print (self.cfg.format('WARN: ' + string, **kwds))

    def shell(self, cmd, **kwds):
        fcmd = self.cfg.format(cmd, **kwds)
        self.info('shell: ' + fcmd)
        return check_call(fcmd, shell=True)

    def command(self, cmd, **kwds):
        fcmd = self.cfg.format(cmd,**kwds)
        self.info('shell: ' + fcmd)
        return check_output(fcmd, shell=True)

    def find_file(self, filename, **kwds):
        filename = self.cfg.format(filename, **kwds)
        if filename.startswith('/'):
            return filename
        maybe = os.path.join(thisdir, filename)
        if os.path.exists(maybe):
            return maybe
        raise RuntimeError("No such file or directory: %s" % filename)

    def filter_template(self, template, destination, **kwds):
        destination = self.cfg.format(destination,**kwds)

        if os.path.exists(destination):
            self.warn('file exists: %s' % destination)
            return
        template = self.find_file(template, **kwds)

        self.info('filtering %s -> %s' % (os.path.basename(template), destination))

        text = open(template).read()
        try:
            newtext = self.cfg.format(text)
        except KeyError:
            self.warn("format filtering failed, trying interpolation on %s" % template)
            newtext = text % self.cfg.asdict()

        open(destination, 'w').write(newtext)


    def install_docdb_files(self):
        if os.path.exists(self.cfg.srcdir):
            self.info ('source already installed at {srcdir}')
        else:
            tag = self.cfg.gittag
            if tag:
                tag = '-b ' + tag
            self.shell('git clone {tag} {giturl} {srcdir}', tag=tag)

        self.shell('mkdir -p {file_root} && chown {web_apache_group}:{web_apache_user} {file_root}')
        if not os.path.exists(self.cfg.format('{file_root}/Static')):
            self.shell('ln -s {srcdir}/DocDB/html {file_root}/Static')
        self.shell('mkdir -p {script_root}')
        if not os.path.exists(self.cfg.format('{script_root}/{web_root}')):
            self.shell('ln -s {srcdir}/DocDB/cgi {script_root}/{web_root}')
        # fixme; what about public/ ?

        for fname in ['ProjectGlobals.pm', 'ProjectMessages.pm',
                      'ProjectRoutines.pm', 'ProjectHelp.xml']:
            self.filter_template(fname+'.template', 
                                 self.cfg.format('{script_root}/{web_root}/{fname}', fname=fname))

        self.filter_template('apache-site.template',
                             self.cfg.format('{root_path}/apache-site.conf'))
        if not os.path.exists(self.cfg.format('/etc/httpd/conf.d/{project_name}.conf')):
            self.shell('ln -s {root_path}/apache-site.conf /etc/httpd/conf.d/{project_name}.conf')

        # fixme: instead of writing this, save the configuration as JSON
        #self.filter_template('my.cnf.template', config['my_cnf'])

        auth_dir = os.path.dirname(self.cfg.auth_file)
        self.shell('mkdir -p {auth_dir}', auth_dir=auth_dir)
        self.shell('touch {auth_file}')  # htpassword is retarded in that it needs a file to exist
        existing = [x.split(':')[0] for x in open(self.cfg.auth_file).readlines()]
        if self.cfg.web_admuser in existing:
            self.warn('web password for {web_admuser} already set in {auth_file}')
        else:
            self.shell('htpasswd -m -b {auth_file} {web_admuser} {web_admpass}')
        if self.cfg.web_rwuser in existing:
            self.warn('web password for {web_rwuser} already set in {auth_file}')
        else:
            self.shell('htpasswd -m -b {auth_file} {web_rwuser} {web_rwpass}')

    def configure_mysql(self):
        root_pass =env('db_root_pass','')
        if self.cfg.db_root_pass:
            dbroot_pass = "-p%s" % self.cfg.db_root_pass

        if self.cfg.db_name in self.command('mysql -uroot -p{root_pass} -hlocalhost -e "show databases;"',root_pass=root_pass):
            self.warn('Database exists: "{db_name}", manually drop to remake.')
            return

        self.filter_template('mysql-init.sql.template', '/tmp/mysql-init.sql')
        self.filter_template('mysql-secgrp.sql.template', '/tmp/mysql-secgrp.sql')
        self.shell('mysql -uroot -hlocalhost -p{root_pass} < /tmp/mysql-init.sql', root_pass=root_pass)
        self.shell('mysql -u{db_admuser} -p{db_admpass} {db_name} < {srcdir}/DocDB/sql/CreateDatabase.SQL')
        self.shell('mysql -u{db_admuser} -p{db_admpass} {db_name} < /tmp/mysql-secgrp.sql')
        self.shell('rm /tmp/mysql-init.sql /tmp/mysql-secgrp.sql')
    
    def save(self, filename):
        filename = self.cfg.save(filename)
        self.shell('chmod 600 %s' % filename)
        self.info('installation data in %s' % filename)
        self.shell('systemctl restart httpd')

def main(filename=None):

    config = Config(filename)
    installer = Install(config)
    installer.install_docdb_files()
    installer.configure_mysql()
    installer.save(filename)

if '__main__' == __name__:
    import sys
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = '*canonical*'
    main(filename)
