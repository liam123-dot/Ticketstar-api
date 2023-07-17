import pymysql
import boto3
import json
import base64
import os
import logging

from DatabaseException import DatabaseException

logger = logging.getLogger()
logger.setLevel(logging.INFO)

host = os.environ.get("HOST")
user = os.environ.get("USER")
password = os.environ.get("PASSWORD")
database = os.environ.get("DATABASE")


def connect_to_db():
    try:
        connection = pymysql.connect(
            host='host.docker.internal',
            user='root',
            password='Redyred358!',
            db='ticketstartest'
        )
        return connection
    except Exception as e:
        logger.error("Error occurred while attempting to connect to database, error: %s", e)
        return None


class Database:
    def __init__(self,):
        # self.secret_name = secret_name
        # self.credentials = self.get_secret()
        self.connection = connect_to_db()

    def get_secret(self):
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager'
        )
        get_secret_value_response = client.get_secret_value(SecretId=self.secret_name)
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])
        return json.loads(secret)

    def execute_select_query(self, query, args=None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, args)
                result = cursor.fetchall()
                logger.info("Database query: %s, results: %s", (query, args), result)
                return result
            except Exception as e:
                logger.error("Error attempting to execute query: %s, error: %s", query, e)
                return None

    def execute_insert_query(self, query, args=None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, args)
                result_id = cursor.lastrowid
                logger.info("Database query: %s", query)
                return result_id
            except Exception as e:
                logger.error("Error attempting to execute query: %s, error: %s", (query, args), e)
                return None

    def execute_update_query(self, query, args=None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, args)
                logger.info("Database query: %s", query)
            except Exception as e:
                logger.error("Error attempting to execute query: %s, error: %s", (query, args), e)
                raise e

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            try:
                self.connection.commit()
                self.connection.close()

                logger.info("Database successfully disconnected")

            except Exception as e:
                logger.error("Error while exiting database connection error: %s", e)
