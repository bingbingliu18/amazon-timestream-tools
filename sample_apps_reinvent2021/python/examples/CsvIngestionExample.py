#!/usr/bin/python

import csv
import random
import time
from utils.QueryUtil import QueryUtil
from utils.WriteUtil import WriteUtil


class CsvIngestionExample:
    def __init__(self, database_name, table_name, write_client, query_client, skip_deletion):
        self.database_name = database_name
        self.table_name = table_name
        self.write_client = write_client
        self.write_util = WriteUtil(self.write_client)
        self.query_client = query_client
        self.query_util = QueryUtil(self.query_client, self.database_name, self.table_name)
        self.skip_deletion = skip_deletion

    def bulk_write_records(self, filepath):
        with open(filepath, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            price = 120

            records = []
            current_time = WriteUtil.current_milli_time()

            # extracting each data row one by one
            for i, row in enumerate(csvreader, 1):
                record = {
                    'Dimensions': [
                        {'Name': row[0], 'Value': row[1]}
                    ],
                    'Time': str(int(current_time) - (i * 50))
                }

                record.update(
                    {
                        'MeasureName': "metrics",
                        'MeasureValueType': "MULTI",
                        'MeasureValues': [
                            {
                                "Name": row[2],
                                "Value": row[3],
                                "Type": row[4],
                            },
                            {
                                "Name": row[5],
                                "Value": str(random.randint(90,150)),
                                "Type": row[7],
                            }
                        ]
                    }
                )
                records.append(record)

                if len(records) == 100:
                    self.__submit_batch(records, i)
                    records = []

            if records:
                self.__submit_batch(records, i)

            print("Ingested %d records" % i)

    def __submit_batch(self, records, n):
        try:
            result = self.write_client.write_records(DatabaseName=self.database_name, TableName=self.table_name,
                                                     Records=records, CommonAttributes={})
            if result and result['ResponseMetadata']:
                print("Processed [%d] records. WriteRecords Status: [%s]" % (n, result['ResponseMetadata']['HTTPStatusCode']))
        except Exception as err:
            print("Error:", err)

    def run_sample_queries(self):
        self.query_util.run_all_queries()

        # Try cancelling a query
        self.query_util.cancel_query()

        # Try a query with multiple pages
        self.query_util.run_query_with_multiple_pages(20000)

    def run(self, csv_file_path):
        if not csv_file_path:
            print('csv_file_path is required')
            return

        try:
            # Create base table and ingest records
            self.write_util.create_database(self.database_name)
            self.write_util.create_table(self.database_name, self.table_name)
            i = 1
            while i == 1:
                self.bulk_write_records(csv_file_path)
                time.sleep(10)
            #self.run_sample_queries()

        finally:
            if not self.skip_deletion:
                self.write_util.delete_table(self.database_name, self.table_name)
                self.write_util.delete_database(self.database_name)

