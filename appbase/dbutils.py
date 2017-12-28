# -*- coding: utf-8 -*-
import os
import glob
import subprocess

from appbase.bootstrap import configure_logger
from os.path import basename
from playhouse.migrate import PostgresqlMigrator, migrate
from appbase.pw import db
import settings

logger = configure_logger('appbase', 'migration.log', settings.DEBUG)
migrator = PostgresqlMigrator(db)
MIGRATIONS_FOLDER_PATH = 'arnold_config/migrations'


def drop_empty_create_table(model):
    '''Drop an empty table and then create a table or Create a table if no table is there'''
    table_name = model._meta.db_table
    if model.table_exists():
        query = "SELECT CASE WHEN EXISTS (SELECT 1 FROM {}) THEN True ELSE False END".format(table_name)
        result = db.execute_sql(query).fetchall()
        if result and result[0] and result[0][0]:
            logger.error('%s table already exists and has data, cant be dropped', table_name)
            raise Exception('Table already exists and has data')
        else:
            try:
                model.drop_table()
                logger.info('%s table dropped', table_name)
                model.create_table()
                logger.info('%s table created', table_name)
            except Exception as e:
                db.rollback()
                logger.error('%s: %s', type(e).__name__, e)
    else:
        model.create_table()
        logger.info('%s table created', table_name)


def add_column(model, column_name, field):
    '''Add column to table if it doesn't exists'''
    table_name = model._meta.db_table
    if model.table_exists():
        query = "SELECT True FROM information_schema.columns WHERE table_name='{}' and column_name='{}'".format(table_name, column_name)
        result = db.execute_sql(query).fetchall()
        if result and result[0] and result[0][0]:
            logger.info('%s column is already in the table %s', column_name, table_name)
        else:
            try:
                migrate(migrator.add_column(table_name, column_name, field))
                logger.info('%s column is added to the table %s', column_name, table_name)
            except Exception as e:
                db.rollback()
                logger.error('%s: %s', type(e).__name__, e)
    else:
        logger.error('No table with name %s found', table_name)


def rename_column(model, old_column_name, new_column_name):
    '''Add column to table if it doesn't exists'''
    table_name = model._meta.db_table
    if model.table_exists():
        try:
            migrate(migrator.rename_column(table_name, old_column_name, new_column_name))
            logger.info('%s column is renamed to %s', old_column_name, new_column_name)
        except Exception as e:
            db.rollback()
            logger.error('%s: %s', (type(e).__name__, e))
    else:
        logger.error('No table with name %s found', table_name)


def delete_column(model, column_name):
    '''Delete column from table if it exists'''
    table_name = model._meta.db_table
    if model.table_exists():
        query = "SELECT True FROM information_schema.columns WHERE table_name='{}' and column_name='{}'".format(table_name, column_name)
        a = db.execute_sql(query).fetchall()
        if a and a[0] and a[0][0]:
            try:
                migrate(migrator.drop_column(table_name, column_name))
                logger.info('%s column is removed from the table %s', column_name, table_name)
            except Exception as e:
                db.rollback()
                logger.error('%s: %s', type(e).__name__, e)
                raise e
        else:
            logger.info('%s column is not present in the table %s', column_name, table_name)
    else:
        logger.error('No table with name %s found', table_name)


def delta():
    files = glob.glob(MIGRATIONS_FOLDER_PATH + '/*.py')
    file_on_master = []
    for file in files:
        cmd = 'git cat-file -e origin/master:{0} && echo True'.format(file)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        head = proc.communicate()[0]
        file_on_master.append(head)

    pos = -2
    for file in file_on_master:
        if file:
            pos += 1

    hash_val = os.path.splitext(basename(files[pos]))[0].split('_')[1]
    cmd = 'git diff {0} -- be/model.py'.format(hash_val)
    os.system(cmd)


def create_next_migration_file():
    proc = subprocess.Popen('git rev-parse HEAD', shell=True, stdout=subprocess.PIPE)
    head = proc.communicate()[0].strip().decode()
    files = glob.glob(MIGRATIONS_FOLDER_PATH + '/*.py')
    for file_name in files:
        if head in file_name:
            print('Migration file already exists: {}'.format(file_name))
            return

    filename = '{:03d}_{}.py'.format(len(files), head)
    filepath = os.path.join(MIGRATIONS_FOLDER_PATH, filename)
    with open(filepath, 'w') as f:
        data = 'def up():\n    pass\n'
        f.write(data)
        print('Migration file created: {}'.format(filename))
