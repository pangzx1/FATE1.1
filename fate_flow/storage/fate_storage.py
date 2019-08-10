#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from typing import Iterable, Dict
from arch.api.utils.core import json_dumps, json_loads
from fate_flow.manager import version_control
from arch.api import eggroll
from fate_flow.entity.runtime_config import RuntimeConfig
import datetime


class FateStorage(object):
    URI_SPLIT_INDEX = None
    URI_JOIN_SEPARATOR = '_'

    @staticmethod
    def init_storage(job_id: str = None):
        eggroll.init(job_id=job_id, mode=RuntimeConfig.WORK_MODE)

    @staticmethod
    def table(namespace: str, name: str, partition: int = 1, persistent: bool = True, create_if_missing: bool = True,
              error_if_exist: bool = False,
              in_place_computing: bool = False):
        data_table = eggroll.table(name=name, namespace=namespace, partition=partition, persistent=persistent,
                                   create_if_missing=create_if_missing, error_if_exist=error_if_exist,
                                   in_place_computing=in_place_computing)
        return data_table

    @staticmethod
    def save_data(kv_data: Iterable, namespace: str, name: str, partition: int = 1, persistent: bool = True,
                  create_if_missing: bool = True, error_if_exist: bool = False,
                  in_version: bool = False, version_log: str = None):
        """
        save data into data table
        :param kv_data:
        :param namespace: table namespace of data table
        :param name: table name of data table
        :param partition: number of partition
        :param create_if_missing:
        :param error_if_exist:
        :return:
            data table instance
        """
        data_table = eggroll.table(name=name, namespace=namespace, partition=partition, persistent=persistent,
                                   create_if_missing=create_if_missing, error_if_exist=error_if_exist)
        data_table.put_all(kv_data)
        if in_version:
            version_log = "[AUTO] save data at %s." % datetime.datetime.now() if not version_log else version_log
            version_control.save_version(name=name, namespace=namespace, version_log=version_log)
        return data_table

    @staticmethod
    def read_data(namespace: str, name: str):
        """
        return data table instance by table name and table name space
        :param namespace: table namespace of data table
        :param name: table name of data table
        :return:
            data table instance
        """
        data_table = FateStorage.table(namespace=namespace, name=name)
        return data_table.collect()

    @staticmethod
    def save_data_table_meta(kv: Dict[str, object], namespace: str, name: str):
        """
        save data table meta information
        :param kv: v should be serialized by JSON
        :param namespace: table namespace of data table
        :param name: table name of data table
        :return:
        """
        meta_data_table = eggroll.table(name='%s.meta' % name,
                                        namespace=namespace,
                                        partition=1,
                                        create_if_missing=True, error_if_exist=False)
        for k, v in kv.items():
            meta_data_table.put(k, json_dumps(v), use_serialize=False)

    @staticmethod
    def get_data_table_meta_value(key: str, namespace: str, name: str):
        """
        get data table meta information
        :param key:
        :param namespace: table namespace of data table
        :param name: table name of data table
        :return:
        """
        meta_data_table = eggroll.table(name='%s.meta' % name,
                                        namespace=namespace,
                                        create_if_missing=True,
                                        error_if_exist=False)
        if meta_data_table:
            value_bytes = meta_data_table.get(key, use_serialize=False)
            if value_bytes:
                return json_loads(value_bytes)
            else:
                return None
        else:
            return None

    @staticmethod
    def get_data_table_meta(namespace: str, name: str):
        """
        get data table meta information
        :param namespace: table namespace of data table
        :param name: table name of data table
        :return:
        """
        meta_data_table = eggroll.table(name='%s.meta' % name,
                                        namespace=namespace,
                                        create_if_missing=True,
                                        error_if_exist=False)
        if meta_data_table:
            metas = dict()
            for k, v in meta_data_table.collect(use_serialize=False):
                metas[k] = json_loads(v)
            return metas
        else:
            return None

    @staticmethod
    def get_data_table_meta_value_by_instance(key, data_table):
        return FateStorage.get_data_table_meta_value(key=key, namespace=data_table._namespace, name=data_table._name)

    @staticmethod
    def get_data_table_meta_by_instance(data_table):
        return FateStorage.get_data_table_meta(namespace=data_table._namespace, name=data_table._name)

    @staticmethod
    def clean_job(namespace, regex_string='*'):
        try:
            eggroll.cleanup(regex_string, namespace=namespace, persistent=False)
        except Exception as e:
            print(e)