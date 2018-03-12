# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import os

from polyaxon_schemas.exceptions import PolyaxonConfigurationError
from polyaxon_schemas.polyaxonfile.specification.base import BaseSpecification
from polyaxon_schemas.polyaxonfile.specification.frameworks import (
    TensorflowSpecification,
    HorovodSpecification,
    MXNetSpecification,
)
from polyaxon_schemas.polyaxonfile.utils import cached_property
from polyaxon_schemas.environments import TensorflowClusterConfig
from polyaxon_schemas.utils import TaskType, Frameworks


class Specification(BaseSpecification):
    """The Base polyaxonfile specification (parsing and validation of Polyaxonfiles/Configurations).

    SECTIONS:
        VERSION: defines the version of the file to be parsed and validated.
        PROJECT: defines the project name this specification belongs to (must be unique).
        SETTINGS: defines the logging, run type and concurrent runs.
        ENVIRONMENT: defines the run environment for experiment.
        DECLARATIONS: variables/modules that can be reused.
        RUN_EXEC: defines the run step where the user can set a docker image to execute
        MODEL: defines the model to use based on the declarative API.
        TRAIN: defines how to train a model and how to read the data.
        EVAL: defines how to evaluate a modela how to read the data
    """

    def __init__(self, experiment, values):
        self._experiment = experiment
        super(Specification, self).__init__(values=values)
        if self.MATRIX in self.headers:
            raise PolyaxonConfigurationError(
                'Specification cannot contain a `matrix` section, you should '
                'use a GroupSpecification instead.')

    @classmethod
    def read(cls, values, experiment=None):
        if isinstance(values, cls):
            return values
        return cls(experiment=experiment, values=values)

    @property
    def experiment(self):
        return self._experiment

    @cached_property
    def experiment_path(self):
        return os.path.join(self.project_path, '{}'.format(self.experiment))

    @cached_property
    def parsed_data(self):
        return self._parsed_data

    @cached_property
    def validated_data(self):
        return self._validated_data

    @cached_property
    def is_runnable(self):
        """Checks of the sections required to run experiment exist."""
        sections = set(self.validated_data.keys())
        if (self.RUN_EXEC in sections or
            {self.MODEL, self.TRAIN} <= sections or
            {self.MODEL, self.EVAL} <= sections):
            return True
        return False

    @cached_property
    def run_exec(self):
        return self.validated_data.get(self.RUN_EXEC, None)

    @cached_property
    def model(self):
        return self.validated_data.get(self.MODEL, None)

    @cached_property
    def environment(self):
        return self.validated_data.get(self.ENVIRONMENT, None)

    @cached_property
    def train(self):
        return self.validated_data.get(self.TRAIN, None)

    @cached_property
    def eval(self):
        return self.validated_data.get(self.EVAL, None)

    @cached_property
    def declarations(self):
        return self.parsed_data.get(self.DECLARATIONS, None)

    @cached_property
    def framework(self):
        if not self.environment:
            return None

        if self.environment.tensorflow:
            return Frameworks.TENSORFLOW

        if self.environment.horovod:
            return Frameworks.HOROVOD

        if self.environment.mxnet:
            return Frameworks.MXNET

    @cached_property
    def cluster_def(self):
        cluster = {
            TaskType.MASTER: 1,
        }
        is_distributed = False
        environment = self.environment

        if not environment:
            return cluster, is_distributed

        if environment.tensorflow:
            return TensorflowSpecification.get_cluster_def(
                cluster=cluster,
                tensorflow_config=environment.tensorflow)
        if environment.horovod:
            return HorovodSpecification.get_cluster_def(
                cluster=cluster,
                horovod_config=environment.horovod)
        if environment.mxnet:
            return MXNetSpecification.get_cluster_def(
                cluster=cluster,
                mxnet_config=environment.mxnet)

    @cached_property
    def total_resources(self):
        environment = self.environment

        if not environment:
            return None

        cluster, is_distributed = self.cluster_def

        # Check if any framework is defined
        if environment.tensorflow:
            return TensorflowSpecification.get_total_resources(
                master_resources=self.master_resources,
                environment=environment,
                cluster=cluster,
                is_distributed=is_distributed
            )

        if environment.horovod:
            return HorovodSpecification.get_total_resources(
                master_resources=self.master_resources,
                environment=environment,
                cluster=cluster,
                is_distributed=is_distributed
            )

        if environment.mxnet:
            return MXNetSpecification.get_total_resources(
                master_resources=self.master_resources,
                environment=environment,
                cluster=cluster,
                is_distributed=is_distributed
            )

        # default value is the master resources
        return self.master_resources

    @cached_property
    def master_resources(self):
        return self.environment.resources if self.environment else None

    def get_local_cluster(self,
                          host='127.0.0.1',
                          master_port=10000,
                          worker_port=11000,
                          ps_port=12000):
        def get_address(port):
            return '{}:{}'.format(host, port)

        cluster_def, is_distributed = self.cluster_def

        cluster_config = {
            TaskType.MASTER: [get_address(master_port)]
        }

        workers = []
        for i in range(cluster_def.get(TaskType.WORKER, 0)):
            workers.append(get_address(worker_port))
            worker_port += 1

        cluster_config[TaskType.WORKER] = workers

        ps = []
        for i in range(cluster_def.get(TaskType.PS, 0)):
            ps.append(get_address(ps_port))
            ps_port += 1

        cluster_config[TaskType.PS] = ps

        return TensorflowClusterConfig.from_dict(cluster_config)

    def get_cluster(self, **kwargs):
        if self.is_local:
            return self.get_local_cluster(**kwargs)