# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

K8S_API_VERSION_V1 = 'v1'
K8S_PERSISTENT_VOLUME_KIND = 'PersistentVolume'
K8S_PERSISTENT_VOLUME_CLAIM_KIND = 'PersistentVolumeClaim'
K8S_CONFIG_MAP_KIND = 'ConfigMap'
DOCKER_IMAGE = 'plx'
ENV_VAR_TEMPLATE = '{name: "{var_name}", value: "{var_value}"}'
DATA_VOLUME = 'data'
LOGS_VOLUME = 'logs'
TMP_VOLUME = 'tmp'
POLYAXON_FILES_VOLUME = 'plx_files'
VOLUME_NAME = 'pv-{vol_name}'
GPU_TEMPLATE = '{alpha.kubernetes.io/nvidia-gpu: {gpu}'
CONFIG_MAP_CLUSTER_NAME = '{project}-{experiment}-cluster'
TASK_NAME = '{project}-{experiment}-{task_type}{task_id}'
TASK_LABELS = ('project: "{project}", '
               'experiment: "{experiment}", '
               'task_type: "{task_type}", '
               'task_id: "{task_id}", '
               'task: "{task_name}"')
POD_CONTAINER_TASK_NAME = '{task_type}{task_id}'