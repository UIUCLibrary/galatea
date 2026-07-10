"""Speedwagon plugin for Galatea."""

from typing import Dict, Type, Any

import speedwagon.workflow
from galatea.gui.workflows import (
    authorized_terms_workflows,
    clean_tsv_workflows,
    merge_data_workflows,
)


@speedwagon.hookimpl
def registered_workflows() -> Dict[str, Type[speedwagon.Workflow[Any]]]:
    """Register the workflows used by this plugin."""
    return {
        "Authorized Terms: Check": authorized_terms_workflows.AuthorizedTermsCheck,
        "Authorized Terms: New Transformation file": authorized_terms_workflows.NewTransformationFile,
        "Authorized Terms: Resolve": authorized_terms_workflows.ResolveAuthorizedTerms,
        "Clean TSV": clean_tsv_workflows.CleanTsv,
        "Merge Data: Initialize GetMarc Mapper File": merge_data_workflows.GetMarcInitMapper,
        "Merge Data: Merge from GetMarc": merge_data_workflows.GetMarcMerge,
    }
