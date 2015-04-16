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
config_dir          = '/opt/fabric/config/'
env.app_dir         = '/opt/application'
env.virtual_env_dir = '/opt/virtualenvs/application'
env.activate        = 'source ' + env.virtual_env_dir + '/bin/activate'

@_contextmanager
def virtualenv():
    with prefix(env.activate):
        yield

def loadenv(environment = ''):
    """Loads an environment config file for role definitions"""
    with open(config_dir + environment + '.yaml', 'r') as f:
        env.config = yaml.load(f)
        env.roledefs = env.config['roledefs']

@roles('application')
def setup():
    """Sets up our application virtualenv"""
    if not exists(env.virtual_env_dir):
        run('virtualenv ' + env.virtual_env_dir)
    if not exists(env.app_dir + '/builds'):
        run('mkdir -p ' + env.app_dir + '/builds')

@roles('application')
def deploy(version='master'):
    """Deploys payment code to application server"""
    if not exists(env.app_dir):
        setup()
    with lcd(env.workspace):
        local('rm -rf fabric-example *.tar.gz')
        local('/usr/bin/git clone https://github.com:disassembler/fabric-examples.git')
        env.release = time.strftime('%Y%m%d%H%M%S')
        with lcd('fabric-examples'):
            local('git checkout ' + version)
            local('git archive --format=tar ' + version + ' | gzip > ../application-' + env.release + '.tar.gz')
        put('application-' + env.release + '.tar.gz', '/tmp/')
    run('mkdir -p ' + env.app_dir + '/builds/' + env.release)
    with cd(env.app_dir + '/builds/' + env.release):
        run('tar -zxvf /tmp/payment-' + env.release + '.tar.gz')
    run('rm ' + env.app_dir + '/current')
    run('ln -sf ' + env.app_dir + '/builds/' + env.release + ' ' + env.app_dir + '/current')
    with cd(env.app_dir + '/current'):
        with virtualenv():
            run('pip install -r requirements.txt')
