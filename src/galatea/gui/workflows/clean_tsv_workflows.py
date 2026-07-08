"""Clean tsv Speedwagon workflows."""

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

import galatea.command_descriptions
from galatea.clean_tsv import clean_tsv
from . import shared_validators

if TYPE_CHECKING:
    from speedwagon.validators import AbsOutputValidation
    from speedwagon.workflow import UserData

__all__ = ["CleanTsv"]

# =============================================================================
# WORKFLOW: "Clean TSV"
#

# -----------------------------------------------------------------------------
# Type Hints

CleanTsvUserArgs = TypedDict("CleanTsvUserArgs", {"Source .tsv": str})


class CleanTsvTaskMetadata(TypedDict):
    """Clean Tsv task metadata.

    source: source .tsv
    destination: output .tsv
    """

    source: str
    destination: str


# -----------------------------------------------------------------------------
# Workflow Class


class CleanTsv(speedwagon.Workflow[CleanTsvUserArgs]):
    """Cleaning tsv workflow."""

    name = "Clean TSV"
    description = galatea.command_descriptions.CLEAN_TSV_DESC

    def discover_task_metadata(
        self,
        initial_results: List[Any],
        additional_data: Mapping[str, Any],
        user_args: CleanTsvUserArgs,
    ) -> List[CleanTsvTaskMetadata]:
        """Discover task metadata."""
        return [
            {
                "source": user_args["Source .tsv"],
                "destination": user_args["Source .tsv"],
            }
        ]

    @staticmethod
    def get_job_validations(
        label: str,
    ) -> List[
        Tuple[
            AbsOutputValidation,
            Optional[Callable[[CleanTsvUserArgs, UserData], bool]],
        ]
    ]:
        """Get validations for this job option."""
        validations: List[
            Tuple[
                AbsOutputValidation,
                Optional[Callable[[CleanTsvUserArgs, UserData], bool]],
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

    def job_options(self) -> List[speedwagon.workflow.AbsOutputOptionDataType]:
        """Job options."""
        source_tsv = speedwagon.workflow.FileSelectData(
            "Source .tsv", required=True
        )
        source_tsv.filter = "Tab-Separated Value (\\*.tsv)"
        job_options: List[speedwagon.workflow.AbsOutputOptionDataType] = [
            source_tsv
        ]
        for job_option in job_options:
            for validation in self.get_job_validations(job_option.label):
                job_option.add_validation(*validation)
        return job_options

    def create_new_task(
        self, task_builder: TaskBuilder, job_args: CleanTsvTaskMetadata
    ) -> None:
        """Create new task."""
        task_builder.add_subtask(
            clean_tsv_task(
                pathlib.Path(job_args["source"]),
                pathlib.Path(job_args["destination"]),
            )
        )

    @classmethod
    def generate_report(
        cls, results: List[Result], user_args: CleanTsvUserArgs
    ) -> Optional[str]:
        """Generate report."""
        return "Clean TSV - Done"


# -----------------------------------------------------------------------------
# Task Function


@speedwagon.tasks.workflow_task(description="Cleaning tsv")
def clean_tsv_task(source: pathlib.Path, dest: pathlib.Path):
    clean_tsv(source, dest)
