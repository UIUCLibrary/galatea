"""Speedwagon Workflows for Merging data."""

from __future__ import annotations

import pathlib
import typing
from typing import (
    Any,
    List,
    Mapping,
    TypedDict,
    Optional,
    Tuple,
    Callable,
    TYPE_CHECKING,
)

import speedwagon.workflow
from galatea import merge_data
from speedwagon.tasks import TaskBuilder, Result
from speedwagon.workflow import AbsOutputOptionDataType

import galatea.command_descriptions
from . import shared_validators

if TYPE_CHECKING:
    from speedwagon.validators import AbsOutputValidation
    from speedwagon.workflow import UserData

__all__ = ["GetMarcInitMapper", "GetMarcMerge"]

OPEN_FILE_PATTERN_MATCHING_TSV = "Tab-Separated Value (\\*.tsv)"
OPEN_FILE_PATTERN_MATCHING_MAPPER_TOML = "Mapper Toml File (\\*.toml)"

# =============================================================================
# WORKFLOW: "Merge Data: Initialize GetMarc Mapper File"
#

# -----------------------------------------------------------------------------
# Type Hints
GetMarcInitMapperArgs = TypedDict(
    "GetMarcInitMapperArgs",
    {
        "Source .tsv": str,
        "Output mapper toml file": str,
    },
)
GetMarcInitMapperArgsTaskMetadata = TypedDict(
    "GetMarcInitMapperArgsTaskMetadata", {"source": str, "output": str}
)


# -----------------------------------------------------------------------------
# Workflow Class


class GetMarcInitMapper(speedwagon.Workflow[GetMarcInitMapperArgs]):
    """Workflow for creating an initial mapper for merging with GetMarc."""

    name = "Merge Data: Initialize GetMarc Mapper File"
    description = (
        galatea.command_descriptions.MERGE_DATA_FROM_GETMARC_INIT_MAPPER_DESC
    )

    def discover_task_metadata(
        self,
        initial_results: List[Any],
        additional_data: Mapping[str, Any],
        user_args: GetMarcInitMapperArgs,
    ) -> List[GetMarcInitMapperArgsTaskMetadata]:
        """Discover the task metadata from the initial results."""
        return [
            {
                "source": user_args["Source .tsv"],
                "output": user_args["Output mapper toml file"],
            }
        ]

    @staticmethod
    def get_job_validations(
        label: str,
    ) -> List[
        Tuple[
            AbsOutputValidation,
            Optional[Callable[[GetMarcInitMapperArgs, UserData], bool]],
        ]
    ]:
        """Get validations for this job option."""
        validations: List[
            Tuple[
                speedwagon.validators.AbsOutputValidation,
                Optional[Callable[[GetMarcInitMapperArgs, UserData], bool]],
            ]
        ] = []
        match label:
            case "Source .tsv":
                not_empty_value = shared_validators.ValidateValueIsNotEmpty()
                validations.append((not_empty_value, None))
                validations.append((
                    shared_validators.ValidateFileExtension(".tsv"),
                    lambda value, _: (
                        not_empty_value.investigate(value, {}) == []
                        if isinstance(value, str)
                        else False
                    ),
                ))
            case "Output mapper toml file":
                not_empty_value = shared_validators.ValidateValueIsNotEmpty()
                validations.append((not_empty_value, None))
                validations.append((
                    shared_validators.ValidateFileExtension(".toml"),
                    lambda value, _: (
                        not_empty_value.investigate(value, {}) == []
                        if isinstance(value, str)
                        else False
                    ),
                ))
        return validations

    def job_options(self) -> List[speedwagon.workflow.AbsOutputOptionDataType]:
        """Get job options for this workflow.

        This includes:
            * "Source .tsv"
            * "Output mapper toml file"
        """
        source_tsv = speedwagon.workflow.FileSelectData(
            "Source .tsv", required=True
        )
        source_tsv.filter = OPEN_FILE_PATTERN_MATCHING_TSV

        output_toml_file = speedwagon.workflow.FileSave(
            "Output mapper toml file", required=True
        )
        output_toml_file.filter = OPEN_FILE_PATTERN_MATCHING_MAPPER_TOML

        job_options = [source_tsv, output_toml_file]
        for job_option in job_options:
            for validation in self.get_job_validations(job_option.label):
                job_option.add_validation(*validation)
        return job_options

    def create_new_task(
        self,
        task_builder: TaskBuilder,
        job_args: GetMarcInitMapperArgsTaskMetadata,
    ) -> None:
        """Create a new task."""
        task_builder.add_subtask(
            generate_mapping_file_for_tsv_task(
                job_args["source"], job_args["output"]
            )
        )

    @classmethod
    def generate_report(
        cls, results: List[Result], user_args: GetMarcInitMapperArgs
    ) -> Optional[str]:
        """Generate a report for the given results."""
        return f"Created new map file: {results[0].data['new_toml_file']}"


# -----------------------------------------------------------------------------
# Task Function


@speedwagon.tasks.workflow_task(description="Generating mapping file")
def generate_mapping_file_for_tsv_task(source, output):
    merge_data.generate_mapping_file_for_tsv(
        pathlib.Path(source), pathlib.Path(output)
    )
    return {"new_toml_file": output}


# =============================================================================
# WORKFLOW: "Merge Data: Merge from GetMarc"
#

# -----------------------------------------------------------------------------
# Type Hints
GetMarcMergeArgs = TypedDict(
    "GetMarcMergeArgs",
    {
        "Source metadata .tsv file": str,
        "Mapper .toml file": str,
        "Output .tsv": str,
    },
)
GetMarcMergeTaskMetadata = TypedDict(
    "GetMarcMergeTaskMetadata",
    {
        "get_marc_url": str,
        "source_tsv": str,
        "mapper_toml": str,
        "output_tsv": str,
    },
)


class GetMarcMerge(speedwagon.Workflow[GetMarcMergeArgs]):
    """Speedwagon Workflow for merging metadata from GetMarc."""

    name = "Merge Data: Merge from GetMarc"
    description = (
        galatea.command_descriptions.MERGE_DATA_FROM_GETMARC_MERGE_DESC
    )

    def discover_task_metadata(
        self,
        initial_results: List[Any],
        additional_data: Mapping[str, Any],
        user_args: GetMarcMergeArgs,
    ) -> List[GetMarcMergeTaskMetadata]:
        """Discover the task metadata from the initial results."""
        get_marc_url = self.get_workflow_configuration_value(
            "GetMarc Server Url"
        )
        return [
            {
                "get_marc_url": typing.cast(str, get_marc_url),
                "source_tsv": user_args["Source metadata .tsv file"],
                "mapper_toml": user_args["Mapper .toml file"],
                "output_tsv": user_args["Output .tsv"],
            }
        ]

    def workflow_options(self) -> List[AbsOutputOptionDataType]:
        """Get the workflow options.

        This get the get marc server url which is required for this workflow.
        """
        return [
            speedwagon.workflow.TextLineEditData(
                "GetMarc Server Url", required=True
            ),
        ]

    @staticmethod
    def get_job_validations(
        label: str,
    ) -> List[
        Tuple[
            speedwagon.validators.AbsOutputValidation,
            Optional[Callable[[GetMarcMergeArgs, UserData], bool]],
        ]
    ]:
        """Get validations for this job option."""
        validations: List[
            Tuple[
                speedwagon.validators.AbsOutputValidation,
                Optional[Callable[[GetMarcMergeArgs, UserData], bool]],
            ]
        ] = []
        match label:
            case "Source metadata .tsv file" | "Output .tsv":
                not_empty_value = shared_validators.ValidateValueIsNotEmpty()
                validations.append((not_empty_value, None))
                validations.append((
                    shared_validators.ValidateFileExtension(".tsv"),
                    lambda value, _: (
                        not_empty_value.investigate(value, {}) == []
                        if isinstance(value, str)
                        else False
                    ),
                ))
            case "Mapper .toml file":
                not_empty_value = shared_validators.ValidateValueIsNotEmpty()
                validations.append((not_empty_value, None))
                validations.append((
                    shared_validators.ValidateFileExtension(".toml"),
                    lambda value, _: (
                        not_empty_value.investigate(value, {}) == []
                        if isinstance(value, str)
                        else False
                    ),
                ))
        return validations

    def job_options(self) -> List[speedwagon.workflow.AbsOutputOptionDataType]:
        """Get job options for this workflow.

        This includes:
            * "Source metadata .tsv file"
            * "Mapper .toml file"
            * "Output .tsv"
        """
        metadata_source_tsv = speedwagon.workflow.FileSelectData(
            "Source metadata .tsv file", required=True
        )
        metadata_source_tsv.filter = OPEN_FILE_PATTERN_MATCHING_TSV

        mapper_toml = speedwagon.workflow.FileSelectData(
            "Mapper .toml file", required=True
        )
        mapper_toml.filter = OPEN_FILE_PATTERN_MATCHING_MAPPER_TOML

        output_tsv = speedwagon.workflow.FileSave("Output .tsv", required=True)

        output_tsv.filter = OPEN_FILE_PATTERN_MATCHING_TSV

        job_options: List[speedwagon.workflow.AbsOutputOptionDataType] = [
            metadata_source_tsv,
            mapper_toml,
            output_tsv,
        ]
        for job_option in job_options:
            for validation in self.get_job_validations(job_option.label):
                job_option.add_validation(*validation)
        return [metadata_source_tsv, mapper_toml, output_tsv]

    def create_new_task(
        self, task_builder: TaskBuilder, job_args: GetMarcMergeTaskMetadata
    ) -> None:
        """Create a get marc merge task."""
        task_builder.add_subtask(
            merge_from_getmarc_task(
                get_marc_url=job_args["get_marc_url"],
                source_tsv=job_args["source_tsv"],
                mapper_toml=job_args["mapper_toml"],
                output_tsv=job_args["output_tsv"],
            ),
        )

    @classmethod
    def generate_report(
        cls, results: List[Result], user_args: GetMarcMergeArgs
    ) -> Optional[str]:
        """Generate report."""
        return f"Get marc merge results at {user_args['Output .tsv']}"


# -----------------------------------------------------------------------------
# Task Function


@speedwagon.tasks.workflow_task(
    description="Merging tsv metadata with data from GetMarc"
)
def merge_from_getmarc_task(
    get_marc_url: str, source_tsv: str, mapper_toml: str, output_tsv: str
):
    merge_data.merge_from_getmarc(
        input_metadata_tsv_file=pathlib.Path(source_tsv),
        output_metadata_tsv_file=pathlib.Path(output_tsv),
        mapping_file=pathlib.Path(mapper_toml),
        get_marc_server=get_marc_url,
        enable_experimental_features=True,
    )
