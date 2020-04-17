from knack.util import CLIError
from azure.cli.core import get_default_cli
import time
import os
import sys

DEFAULT_CLI = get_default_cli()

SERVICE_BINDING_TYPE = [
    'Azure Cosmos DB',
    'Azure Cache for Redis',
    'Azure Database for MySQL'
]

def spring_cloud_handler(resource_group, deployment_id, settings, para_dict):
    # parse the parameter
    asc_name = para_dict['asc_name']
    app_name = para_dict['app_name']
    jar_path = para_dict['jar_path']
    binding_name = para_dict['binding_name']
    binding_type = settings['binding_type']
    if binding_type == SERVICE_BINDING_TYPE[0]:
        resource_id = settings['cosmosdb_resource_id']
        database_name = settings['database_name']
    elif binding_type == SERVICE_BINDING_TYPE[2]:
        username = settings['username']
        key = settings['key']
        resource_id = settings['mysql_resource_id']
        database_name = settings['database_name']
    # check azure spring-cloud service
    parameters = [
        'spring-cloud', 'show',
        '--resource-group', resource_group,
        '--name', asc_name,
        '--output', 'none'
    ]
    try:
        DEFAULT_CLI.invoke(parameters)
    except:
        # not exists, create a new one
        parameters = [
            'spring-cloud', 'create',
            '--name', asc_name,
            '--resource-group', resource_group
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to create Azure Spring Cloud service %s.' % asc_name)
    # create app
    # check if app exists
    parameters = [
        'spring-cloud', 'app', 'show',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group,
        '--output', 'none'
    ]
    try:
        DEFAULT_CLI.invoke(parameters)
    except:
        print('App %s does not exists, creating it...' % app_name)
        parameters = [
            'spring-cloud', 'app', 'create',
            '--name', app_name,
            '--service', asc_name,
            '--resource-group', resource_group,
            '--runtime-version', 'Java_11',
            '--is-public', 'true',
            '--output', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to crreat App %s for Azure Spring Cloud %s.' % (app_name, asc_name))
    finally:
        print('App %s created.' % app_name)
        parameters = [
            'spring-cloud', 'app', 'update',
            '--name', app_name,
            '--service', asc_name,
            '--resource-group', resource_group,
            '--runtime-version', 'Java_11',
            '--output', 'none'
        ]
        if DEFAULT_CLI.invoke(parameters):
            raise CLIError('Fail to update App %s configuration.' % app_name)
    # deploy app
    parameters = [
        'spring-cloud', 'app', 'deploy',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group,
        '--jar-path', jar_path,
        '--output', 'none'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to deploy jar file %s to App %s.' % (jar_path, app_name))
    # binding DB
    parameters = [
        'spring-cloud', 'app', 'binding', 'cosmos', 'add',
        '--api-type', 'sql',
        '--app', app_name,
        '--name', binding_name,
        '--resource-id', resource_id,
        '--service', asc_name,
        '--database-name', database_name,
        '--resource-group', resource_group,
        '--output', 'none'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to bind %s to App %s.' % (resource_id, app_name))
    # restart app
    parameters = [
        'spring-cloud', 'app', 'restart',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group,
        '--output', 'none'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to restart App %s.' % app_name)
    # check app status
    wait = 30
    print('Waiting %d seconds for APP instance running up...' % wait)
    time.sleep(wait)
    parameters = [
        'spring-cloud', 'app', 'show',
        '--name', app_name,
        '--service', asc_name,
        '--resource-group', resource_group,
        '--output', 'none'
    ]
    if DEFAULT_CLI.invoke(parameters):
        raise CLIError('Fail to show App %s status.' % app_name)
    print('App url: %s' % DEFAULT_CLI.result.result['properties']['url'])
