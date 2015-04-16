from fabric.api import *
from fabric.context_managers import settings
from fabric.decorators import roles
from fabric.api import run, cd, env, roles, lcd
from contextlib import contextmanager as _contextmanager
from fabric.contrib.files import exists
from pprint import pprint
from time import sleep
import time
import yaml
import fabric

workspace           = '/tmp/work'
config_dir          = '/Users/sam/scratch/fabric-example/config'
app_dir         = '/opt/application'
virtual_env_dir = '/opt/virtualenvs/application'
activate        = 'source ' + virtual_env_dir + '/bin/activate'
app_repo        = 'https://github.com/disassembler/fabric-example.git'
app_name        = 'fabric-example'

@_contextmanager
def virtualenv():
    with prefix(activate):
        yield

def loadenv(environment = ''):
    """Loads an environment config file for role definitions"""
    with open(config_dir + '/' + environment + '.yml', 'r') as f:
        env.config = yaml.load(f)
        env.roledefs = env.config['roledefs']
        env.user = env.config['user']
        env.password = env.config['password']

@roles('application')
def setup():
    """Sets up our application virtualenv"""
    if not exists(virtual_env_dir):
        sudo('mkdir -p ' + virtual_env_dir)
        sudo('chown -R ' + env.user + ' ' + virtual_env_dir)
        run('virtualenv ' + virtual_env_dir)
    if not exists(app_dir + '/builds'):
        sudo('mkdir -p ' + app_dir + '/builds')
        sudo('chown -R ' + env.user + ' ' + app_dir)

@roles('application')
def deploy(version='master'):
    """Deploys code to application server"""
    if not exists(app_dir):
        setup()
    local('mkdir -p ' + workspace)
    with lcd(workspace):
        local('rm -rf *.tar.gz ' + app_name)
        local('/usr/bin/git clone ' + app_repo + ' ' + app_name)
        release = time.strftime('%Y%m%d%H%M%S')
        with lcd(app_name):
            local('git checkout ' + version)
            local('git archive --format=tar ' + version + ' | gzip > ../application-' + release + '.tar.gz')
        put('application-' + release + '.tar.gz', '/tmp/')
    run('mkdir -p ' + app_dir + '/builds/' + release)
    with cd(app_dir + '/builds/' + release):
        run('tar -zxvf /tmp/application-' + release + '.tar.gz')
    run('rm -f ' + app_dir + '/current')
    run('ln -sf ' + app_dir + '/builds/' + release + ' ' + app_dir + '/current')
    with cd(app_dir + '/current'):
        with virtualenv():
            run('pip install -q -U -r requirements.txt')
