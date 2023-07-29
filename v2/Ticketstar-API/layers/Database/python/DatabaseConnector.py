import pymysql
import boto3
import json
import base64
import os
import logging

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def connect_to_db():
    try:
        database_info = json.loads(get_secret())

        host = database_info['host']
        database = database_info['dbname']
        username = database_info['username']
        password = database_info['password']

        connection = pymysql.connect(
            host=host,
            database=database,
            user=username,
            password=password,
            ssl_ca='/etc/pki/tls/certs/ca-bundle.crt'
        )

        # connection = pymysql.connect(
        #     # host.docker.internal
        #     host='host.docker.internal',
        #     user='root',
        #     password='Redyred358!',
        #     db='ticketstartest'
        # )

        return connection
    except Exception as e:
        logger.error("Error occurred while attempting to connect to database, error: %s", e)
        return None


def get_secret():

    secret_name = "PlanetScaleDatabaseCreds"
    region_name = "eu-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    return secret


class Database:
    def __init__(self,):
        self.connection = connect_to_db()

    def execute_select_query(self, query, args=None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, args)
                result = cursor.fetchall()
                logger.info("Database query: %s, results: %s", (query, args), result)
                return result
            except Exception as e:
                logger.error("Error attempting to execute query: %s, error: %s", query, e)
                raise e

    def execute_insert_query(self, query, args=None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, args)
                result_id = cursor.lastrowid
                logger.info("Database query: %s", (query, args))
                return result_id
            except Exception as e:
                logger.error("Error attempting to execute query: %s, error: %s", (query, args), e)
                raise e

    def execute_update_query(self, query, args=None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, args)
                logger.info("Database query: %s", (query, args))
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
