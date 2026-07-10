"""Authorized terms related workflows."""

from __future__ import annotations

import pathlib
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
import speedwagon
import speedwagon.workflow
from speedwagon.tasks import TaskBuilder, Result
from . import shared_validators

import galatea.command_descriptions
from galatea import validate_authorized_terms, resolve_authorized_terms

if TYPE_CHECKING:
    from speedwagon.validators import AbsOutputValidation
    from speedwagon.workflow import UserData

__all__ = [
    "AuthorizedTermsCheck",
    "NewTransformationFile",
    "ResolveAuthorizedTerms",
]

OPEN_FILE_PATTERN_MATCHING_TSV = "Tab-Separated Value (\\*.tsv)"

# =============================================================================
# WORKFLOW: "Authorized Terms: Check"
#

# -----------------------------------------------------------------------------
# Type Hints
AuthorizedTermsCheckArgs = TypedDict(
    "AuthorizedTermsCheckArgs",
    {"Source .tsv": str},
)
AuthorizedTermsCheckTaskMetadata = TypedDict(
    "AuthorizedTermsCheckTaskMetadata", {"source": str}
)


# -----------------------------------------------------------------------------
# Workflow Class


class AuthorizedTermsCheck(speedwagon.Workflow[AuthorizedTermsCheckArgs]):
    """Authorized Terms Check Workflow."""

    name = "Authorized Terms: Check"
    description = (
        galatea.command_descriptions.AUTHORIZED_TERMS_CHECK_DESCRIPTION
    )

    @staticmethod
    def get_job_validations(
        label: str,
    ) -> List[
        Tuple[
            AbsOutputValidation,
            Optional[Callable[[AuthorizedTermsCheckArgs, UserData], bool]],
        ]
    ]:
        """Get validations for this job option."""
        validations: List[
            Tuple[
                AbsOutputValidation,
                Optional[Callable[[AuthorizedTermsCheckArgs, UserData], bool]],
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
        return validations

    def discover_task_metadata(
        self,
        initial_results: List[Any],
        additional_data: Mapping[str, Any],
        user_args: AuthorizedTermsCheckArgs,
    ) -> List[AuthorizedTermsCheckTaskMetadata]:
        """Discover task metadata for this workflow."""
        return [{"source": user_args["Source .tsv"]}]

    def job_options(self) -> List[speedwagon.workflow.AbsOutputOptionDataType]:
        """Get job options for this workflow.

        This includes:
            * "Source .tsv"
        """
        source_tsv = speedwagon.workflow.FileSelectData(
            "Source .tsv", required=True
        )
        source_tsv.filter = OPEN_FILE_PATTERN_MATCHING_TSV
        for validation in self.get_job_validations("Source .tsv"):
            source_tsv.add_validation(*validation)
        return [source_tsv]

    def create_new_task(  # noqa: B027
        self,
        task_builder: TaskBuilder,
        job_args: AuthorizedTermsCheckTaskMetadata,
    ) -> None:
        """Create task for validating authorized terms."""
        # The following line should be ignored by sonarscanner because sonar
        # doesn't seem to realize that speedwagon.tasks.workflow_task
        # decorator changes the return type to make the function lazily
        # evaluated.
        task_builder.add_subtask(
            validate_authorized_terms_task(job_args["source"])  # NOSONAR
        )

    @classmethod
    def generate_report(
        cls, results: List[Result], user_args: AuthorizedTermsCheckArgs
    ) -> Optional[str]:
        """Generate report for this workflow."""
        return "Authorized Terms Check: completed"


# -----------------------------------------------------------------------------
# Task Function


@speedwagon.tasks.workflow_task(description="Validate authorized terms")
def validate_authorized_terms_task(source: str) -> None:
    """Validate authorized terms."""
    validate_authorized_terms.validate_authorized_terms(pathlib.Path(source))


# =============================================================================
# WORKFLOW: "Authorized Terms: New Transformation file"
#

# -----------------------------------------------------------------------------
# Type Hints

NewTransformationFileArgs = TypedDict(
    "NewTransformationFileArgs", {"File Name": str}
)
NewTransformationFileTaskMetadata = TypedDict(
    "NewTransformationFileTaskMetadata", {"output": str}
)


# -----------------------------------------------------------------------------
# Workflow Class


class NewTransformationFile(speedwagon.Workflow[NewTransformationFileArgs]):
    """Create a new Transformation File Workflow."""

    name = "Authorized Terms: New Transformation file"
    description = galatea.command_descriptions.AUTHORIZED_TERMS_NEW_TRANSFORMATION_FILE_DESCRIPTION

    def discover_task_metadata(
        self,
        initial_results: List[Any],
        additional_data: Mapping[str, Any],
        user_args: NewTransformationFileArgs,
    ) -> List[NewTransformationFileTaskMetadata]:
        """Discover task metadata for this workflow."""
        return [{"output": user_args["File Name"]}]

    def job_options(self) -> List[speedwagon.workflow.AbsOutputOptionDataType]:
        """Get job options for this workflow.

        This includes:
            * "Output .tsv"
        """
        output_tsv = speedwagon.workflow.FileSave("File Name", required=True)

        output_tsv.filter = OPEN_FILE_PATTERN_MATCHING_TSV
        job_options: List[speedwagon.workflow.AbsOutputOptionDataType] = [
            output_tsv
        ]
        for job_option in job_options:
            for validation in self.get_job_validations(job_option.label):
                job_option.add_validation(*validation)
        return job_options

    @staticmethod
    def get_job_validations(
        label: str,
    ) -> List[
        Tuple[
            AbsOutputValidation,
            Optional[Callable[[NewTransformationFileArgs, UserData], bool]],
        ]
    ]:
        """Get validations for this job option."""
        validations: List[
            Tuple[
                AbsOutputValidation,
                Optional[
                    Callable[[NewTransformationFileArgs, UserData], bool]
                ],
            ]
        ] = []
        match label:
            case "File Name":
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
        return validations

    def create_new_task(  # noqa: B027
        self,
        task_builder: TaskBuilder,
        job_args: NewTransformationFileTaskMetadata,
    ) -> None:
        """Create new transformation file task for this workflow."""
        # The following line should be ignored by sonarscanner because sonar
        # doesn't seem to realize that speedwagon.tasks.workflow_task
        # decorator changes the return type to make the function lazily
        # evaluated.
        task_builder.add_subtask(
            create_new_transformation_file_task(job_args["output"])  # NOSONAR
        )

    @classmethod
    def generate_report(
        cls, results: List[Result], user_args: NewTransformationFileArgs
    ) -> Optional[str]:
        """Generate report for this workflow."""
        return "Authorized Terms Check: completed"


# -----------------------------------------------------------------------------
# Task Function


@speedwagon.tasks.workflow_task(description="Create new transformation file")
def create_new_transformation_file_task(output: str) -> None:
    new_file = pathlib.Path(output)
    if new_file.exists():
        new_file.unlink()

    resolve_authorized_terms.create_init_transformation_file(new_file)


# =============================================================================
# WORKFLOW: "Authorized Terms: Resolve"

# -----------------------------------------------------------------------------
# Type Hints

ResolveAuthorizedTermsArgs = TypedDict(
    "ResolveAuthorizedTermsArgs",
    {
        "Source .tsv": str,
        "Transformation .tsv file": str,
        "Output .tsv": str,
    },
)
ResolveAuthorizedTermsTaskMetadata = TypedDict(
    "ResolveAuthorizedTermsTaskMetadata",
    {
        "source_file": str,
        "transformer_file": str,
        "output_file": str,
    },
)


# -----------------------------------------------------------------------------
# Workflow Class


class ResolveAuthorizedTerms(speedwagon.Workflow[ResolveAuthorizedTermsArgs]):
    """Resolve Authorized Terms Workflow."""

    name = "Authorized Terms: Resolve"
    description = (
        galatea.command_descriptions.AUTHORIZED_TERMS_RESOLVE_DESCRIPTION
    )

    def discover_task_metadata(
        self,
        initial_results: List[Any],
        additional_data: Mapping[str, Any],
        user_args: ResolveAuthorizedTermsArgs,
    ) -> List[ResolveAuthorizedTermsTaskMetadata]:
        """Discover task metadata for this workflow."""
        return [
            {
                "source_file": user_args["Source .tsv"],
                "transformer_file": user_args["Transformation .tsv file"],
                "output_file": user_args["Output .tsv"],
            }
        ]

    def job_options(self) -> List[speedwagon.workflow.AbsOutputOptionDataType]:
        """Get job options for this workflow.

        This includes:
            * "Source .tsv"
            * "Transformation .tsv file"
            * "Output .tsv"
        """
        source_tsv = speedwagon.workflow.FileSelectData(
            "Source .tsv", required=True
        )
        source_tsv.filter = OPEN_FILE_PATTERN_MATCHING_TSV

        transformation_file = speedwagon.workflow.FileSelectData(
            "Transformation .tsv file", required=True
        )

        transformation_file.filter = OPEN_FILE_PATTERN_MATCHING_TSV

        output_tsv = speedwagon.workflow.FileSave("Output .tsv", required=True)

        output_tsv.filter = OPEN_FILE_PATTERN_MATCHING_TSV

        job_options = [source_tsv, transformation_file, output_tsv]
        for job_option in job_options:
            for validation in self.get_job_validations(job_option.label):
                job_option.add_validation(*validation)
        return job_options

    def create_new_task(  # noqa: B027
        self,
        task_builder: TaskBuilder,
        job_args: ResolveAuthorizedTermsTaskMetadata,
    ) -> None:
        """Create a new task."""
        # The following line should be ignored by sonarscanner because sonar
        # doesn't seem to realize that speedwagon.tasks.workflow_task
        # decorator changes the return type to make the function lazily
        # evaluated.
        task_builder.add_subtask(
            resolve_authorized_terms_task(  # NOSONAR
                job_args["source_file"],
            )
        )

    @classmethod
    def generate_report(
        cls, results: List[Result], user_args: ResolveAuthorizedTermsArgs
    ) -> Optional[str]:
        """Generate a report."""
        return "Authorized Terms: Resolve"

    @staticmethod
    def get_job_validations(
        label: str,
    ) -> List[
        Tuple[
            AbsOutputValidation,
            Optional[Callable[[ResolveAuthorizedTermsArgs, UserData], bool]],
        ]
    ]:
        """Get validations for this job option."""
        validations: List[
            Tuple[
                AbsOutputValidation,
                Optional[
                    Callable[[ResolveAuthorizedTermsArgs, UserData], bool]
                ],
            ]
        ] = []
        match label:
            case "Source .tsv" | "Transformation .tsv file" | "Output .tsv":
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
        return validations


# -----------------------------------------------------------------------------
# Task Function


@speedwagon.tasks.workflow_task(description="Resolving Authorized Terms")
def resolve_authorized_terms_task(
    source_tsv, transformation_tsv_file, output_tsv
) -> None:
    resolve_authorized_terms.resolve_authorized_terms(
        input_tsv=source_tsv,
        transformation_file=transformation_tsv_file,
        output_file=output_tsv,
    )
