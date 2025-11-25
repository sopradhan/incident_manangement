"""
Healing Tools
Tools for REFRAG self-healing: heatmap analysis, quality detection, reindexing
NO RAW SQL - All queries through model methods
"""
import json
import hashlib
import sqlite3
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from ...database.models.tracking_model import QueryHeatmapModel, HealingOperationModel, SyntheticQueryModel
from ...database.models.embedding_model import EmbeddingMetadataModel
from ...database.models.document_model import DocumentModel


# All healing tools have been removed as they were not used anywhere in the codebase
# This file is kept for future healing functionality
