"""Canonical ontology entity definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GeographicEntity:
    entity_id: str
    geography_type: str  # e.g., tract, block_group, zip, msa
    name: Optional[str] = None
    county_fips: Optional[str] = None
    state_fips: Optional[str] = None


@dataclass
class DemographicEntity:
    entity_id: str
    geography_entity_id: str
    period: str
    population: Optional[float] = None
    median_income: Optional[float] = None


@dataclass
class ApartmentMarketEntity:
    entity_id: str
    geography_entity_id: str
    period: str
    rent_index: Optional[float] = None
    rent_growth_1m: Optional[float] = None
    rent_growth_12m: Optional[float] = None


@dataclass
class EconomicEntity:
    entity_id: str
    geography_entity_id: str
    period: str
    unemployment_rate: Optional[float] = None
    inflation_rate: Optional[float] = None
