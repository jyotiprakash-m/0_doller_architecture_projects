"""
Generation Engine — AI-powered synthetic data generation.
Uses local Ollama LLM to analyze schemas and create smart generation plans,
then Faker + Python execute the plan for high-performance bulk data creation.

Architecture:
  1. LLM analyzes schema → outputs a generation plan (column semantics, distributions)
  2. Python + Faker execute the plan → bulk inserts into DuckDB
  3. Referential integrity maintained via topological sort of FK dependencies
"""

from __future__ import annotations

import json
import logging
import re
import time
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timedelta, date

from faker import Faker
from llama_index.llms.ollama import Ollama

from config import LLM_MODEL, LLM_REQUEST_TIMEOUT, LLM_TEMPERATURE, OLLAMA_BASE_URL, DEFAULT_BATCH_SIZE
from services.duckdb_store import duckdb_store
from services import db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_RETRIES = 2
_RETRY_DELAY = 1.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ColumnPlan:
    """Plan for generating a single column's data."""
    name: str
    data_type: str
    faker_method: str  # e.g., "name", "email", "random_int", "date_between"
    faker_args: dict = field(default_factory=dict)
    is_primary_key: bool = False
    is_foreign_key: bool = False
    fk_reference: Optional[str] = None  # "table.column"
    unique: bool = False
    nullable: bool = True
    null_probability: float = 0.0


@dataclass
class TablePlan:
    """Plan for generating an entire table's data."""
    name: str
    columns: list[ColumnPlan]
    row_count: int
    depends_on: list[str] = field(default_factory=list)  # Tables this depends on (FK refs)


@dataclass
class GenerationPlan:
    """Full plan for generating all tables in order."""
    tables: list[TablePlan]
    generation_order: list[str]  # Topologically sorted table names
    total_rows: int


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SCHEMA_ANALYSIS_PROMPT = """\
You are a database expert and synthetic data specialist. Analyze the following database schema \
and determine the best Faker method to generate realistic data for each column.

--- SCHEMA ---
{schema}
--- END ---

For each column, determine:
1. The semantic meaning (e.g., "email" column should use faker.email())
2. The best Faker method to generate realistic data
3. Any arguments for the Faker method
4. If the column should have null values and what probability

Available Faker methods (use these exact names):
- "name" - full person name
- "first_name" - first name only
- "last_name" - last name only
- "email" - email address
- "phone_number" - phone number
- "address" - full address
- "street_address" - street only
- "city" - city name
- "state" - state name
- "country" - country name
- "zipcode" - zip/postal code
- "company" - company name
- "job" - job title
- "text" - paragraph of text
- "sentence" - single sentence
- "word" - single word
- "url" - website URL
- "ipv4" - IP address
- "user_name" - username
- "password" - password hash
- "uuid4" - UUID
- "random_int" - random integer (args: {{"min": 0, "max": 9999}})
- "random_float" - random float (args: {{"min": 0, "max": 9999, "right_digits": 2}})
- "pricetag" - price string
- "currency_code" - currency code
- "boolean" - true/false
- "date_between" - date (args: {{"start_date": "-5y", "end_date": "today"}})
- "date_time_between" - datetime (args: {{"start_date": "-5y", "end_date": "now"}})
- "past_date" - date in the past
- "future_date" - date in the future
- "iso8601" - ISO 8601 timestamp
- "color_name" - color name
- "hex_color" - hex color code
- "file_name" - file name
- "mime_type" - MIME type
- "credit_card_number" - CC number
- "iban" - IBAN
- "license_plate" - license plate
- "ean13" - barcode
- "catch_phrase" - business catch phrase
- "bs" - business buzzword
- "paragraph" - paragraph text

Respond with ONLY a JSON array. Each item:
{{
    "table_name": "table_name",
    "column_name": "column_name",
    "faker_method": "method_name",
    "faker_args": {{}},
    "null_probability": 0.0
}}

Respond with ONLY the JSON array, no preamble, no markdown.\
"""

_DDL_PARSE_PROMPT = """\
You are a SQL expert. Parse the following SQL DDL statements and extract the table definitions.

--- SQL DDL ---
{ddl}
--- END ---

Return a JSON array of table definitions. Each item:
{{
    "name": "table_name",
    "columns": [
        {{
            "name": "column_name",
            "data_type": "varchar|integer|bigint|float|double|boolean|date|timestamp|text|uuid",
            "nullable": true,
            "primary_key": false,
            "unique": false,
            "foreign_key": null,
            "default_value": null
        }}
    ]
}}

For foreign_key, use format "referenced_table.referenced_column" or null if not a FK.

Respond with ONLY the JSON array. No explanation, no markdown fences.\
"""


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

class LLMError(RuntimeError):
    """Raised when the LLM cannot be reached after all retries."""


def _extract_json(text: str) -> Any:
    """Best-effort extraction of a JSON value from raw LLM output."""
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Markdown code fence
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Greedy array / object match
    for pattern in (r"\[[\s\S]*\]", r"\{[\s\S]*\}"):
        m = re.search(pattern, text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass

    raise json.JSONDecodeError("No valid JSON found", text, 0)


# ---------------------------------------------------------------------------
# GenerationEngine
# ---------------------------------------------------------------------------

class GenerationEngine:
    """
    AI-powered synthetic data generation engine.
    Uses local Ollama LLM for schema analysis, Faker for bulk data generation.
    """

    def __init__(self) -> None:
        self._llm: Optional[Ollama] = None

    def _get_llm(self) -> Ollama:
        if self._llm is None:
            self._llm = Ollama(
                model=LLM_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=LLM_TEMPERATURE,
                request_timeout=LLM_REQUEST_TIMEOUT,
            )
        return self._llm

    def _call_llm(self, prompt: str) -> str:
        """Call the local LLM, retrying on failure."""
        llm = self._get_llm()
        last_exc: Exception = RuntimeError("No attempts made")

        for attempt in range(1, _MAX_RETRIES + 2):
            try:
                response = llm.complete(prompt)
                return str(response)
            except Exception as exc:
                last_exc = exc
                if attempt <= _MAX_RETRIES:
                    logger.warning("LLM call failed (attempt %d/%d): %s", attempt, _MAX_RETRIES + 1, exc)
                    time.sleep(_RETRY_DELAY * attempt)
                else:
                    logger.error("LLM call failed after %d attempts: %s", _MAX_RETRIES + 1, exc)

        raise LLMError(f"LLM unavailable after {_MAX_RETRIES + 1} attempts") from last_exc

    # ------------------------------------------------------------------
    # Schema Parsing
    # ------------------------------------------------------------------

    def parse_ddl(self, ddl: str) -> list[dict]:
        """
        Parse SQL DDL into structured table definitions using LLM.
        Falls back to regex parsing if LLM fails.
        """
        try:
            raw = self._call_llm(_DDL_PARSE_PROMPT.format(ddl=ddl))
            parsed = _extract_json(raw)
            if isinstance(parsed, list):
                return parsed
        except (LLMError, json.JSONDecodeError) as e:
            logger.warning(f"LLM DDL parsing failed, using fallback: {e}")

        return self._fallback_parse_ddl(ddl)

    def _fallback_parse_ddl(self, ddl: str) -> list[dict]:
        """Regex-based fallback DDL parser for when Ollama is unavailable."""
        tables = []
        # Match CREATE TABLE statements
        table_pattern = re.compile(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?(\w+)[`"\']?\s*\((.*?)\);',
            re.IGNORECASE | re.DOTALL
        )

        for match in table_pattern.finditer(ddl):
            table_name = match.group(1)
            columns_str = match.group(2)
            columns = []

            # Parse individual column definitions
            for line in columns_str.split(","):
                line = line.strip()
                if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "INDEX", "CONSTRAINT", "CHECK")):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                col_name = parts[0].strip('`"\'')
                col_type = parts[1].strip('`"\'').lower()

                # Normalize types
                type_map = {
                    "int": "integer", "serial": "integer", "bigserial": "bigint",
                    "varchar": "varchar", "char": "varchar", "character": "varchar",
                    "text": "text", "bool": "boolean", "float4": "float",
                    "float8": "double", "numeric": "float", "real": "float",
                    "datetime": "timestamp", "timestamptz": "timestamp",
                }
                # Strip parenthesized precision
                base_type = re.sub(r'\(.*?\)', '', col_type)
                col_type = type_map.get(base_type, base_type)

                line_upper = line.upper()
                is_pk = "PRIMARY KEY" in line_upper
                is_unique = "UNIQUE" in line_upper
                is_not_null = "NOT NULL" in line_upper

                # Detect foreign key references
                fk_ref = None
                fk_match = re.search(r'REFERENCES\s+[`"\']?(\w+)[`"\']?\s*\([`"\']?(\w+)', line, re.IGNORECASE)
                if fk_match:
                    fk_ref = f"{fk_match.group(1)}.{fk_match.group(2)}"

                columns.append({
                    "name": col_name,
                    "data_type": col_type,
                    "nullable": not is_not_null and not is_pk,
                    "primary_key": is_pk,
                    "unique": is_unique,
                    "foreign_key": fk_ref,
                    "default_value": None,
                })

            if columns:
                tables.append({"name": table_name, "columns": columns})

        return tables

    # ------------------------------------------------------------------
    # Generation Plan
    # ------------------------------------------------------------------

    def create_generation_plan(self, tables: list[dict], row_count: int) -> GenerationPlan:
        """
        Create a generation plan using LLM for semantic column analysis.
        Falls back to heuristic-based plan if LLM fails.
        """
        # Try LLM-based analysis
        column_plans_map = {}
        try:
            schema_desc = json.dumps(tables, indent=2)
            raw = self._call_llm(_SCHEMA_ANALYSIS_PROMPT.format(schema=schema_desc))
            parsed = _extract_json(raw)

            if isinstance(parsed, list):
                for item in parsed:
                    key = f"{item.get('table_name', '')}.{item.get('column_name', '')}"
                    column_plans_map[key] = item
                logger.info(f"LLM analyzed {len(column_plans_map)} columns for generation plan")
        except (LLMError, json.JSONDecodeError) as e:
            logger.warning(f"LLM schema analysis failed, using heuristic fallback: {e}")

        # Build table plans
        table_plans = []
        for table_def in tables:
            table_name = table_def["name"]
            col_plans = []
            depends_on = []

            for col_def in table_def["columns"]:
                col_name = col_def["name"]
                key = f"{table_name}.{col_name}"
                llm_plan = column_plans_map.get(key, {})

                # Determine faker method
                faker_method = llm_plan.get("faker_method") or self._infer_faker_method(col_def)
                faker_args = llm_plan.get("faker_args", {})
                null_prob = llm_plan.get("null_probability", 0.0)

                # Track FK dependencies
                fk_ref = col_def.get("foreign_key")
                if fk_ref:
                    ref_table = fk_ref.split(".")[0]
                    if ref_table != table_name:
                        depends_on.append(ref_table)

                col_plans.append(ColumnPlan(
                    name=col_name,
                    data_type=col_def.get("data_type", "varchar"),
                    faker_method=faker_method,
                    faker_args=faker_args,
                    is_primary_key=col_def.get("primary_key", False),
                    is_foreign_key=fk_ref is not None,
                    fk_reference=fk_ref,
                    unique=col_def.get("unique", False),
                    nullable=col_def.get("nullable", True),
                    null_probability=null_prob if col_def.get("nullable", True) else 0.0,
                ))

            table_plans.append(TablePlan(
                name=table_name,
                columns=col_plans,
                row_count=row_count,
                depends_on=list(set(depends_on)),
            ))

        # Topological sort for FK dependencies
        generation_order = self._topological_sort(table_plans)
        total_rows = row_count * len(table_plans)

        return GenerationPlan(
            tables=table_plans,
            generation_order=generation_order,
            total_rows=total_rows,
        )

    def _infer_faker_method(self, col_def: dict) -> str:
        """
        Heuristic fallback: infer Faker method from column name and type.
        This runs when the LLM is unavailable.
        """
        name = col_def.get("name", "").lower()
        dtype = col_def.get("data_type", "").lower()

        # Name-based inference
        name_map = {
            "email": "email",
            "mail": "email",
            "first_name": "first_name",
            "firstname": "first_name",
            "last_name": "last_name",
            "lastname": "last_name",
            "name": "name",
            "full_name": "name",
            "username": "user_name",
            "user_name": "user_name",
            "phone": "phone_number",
            "telephone": "phone_number",
            "mobile": "phone_number",
            "address": "address",
            "street": "street_address",
            "city": "city",
            "state": "state",
            "country": "country",
            "zip": "zipcode",
            "zipcode": "zipcode",
            "postal_code": "zipcode",
            "company": "company",
            "organization": "company",
            "job": "job",
            "title": "job",
            "job_title": "job",
            "url": "url",
            "website": "url",
            "ip": "ipv4",
            "ip_address": "ipv4",
            "password": "password",
            "description": "paragraph",
            "bio": "paragraph",
            "about": "paragraph",
            "comment": "sentence",
            "note": "sentence",
            "notes": "paragraph",
            "color": "color_name",
            "price": "random_float",
            "amount": "random_float",
            "cost": "random_float",
            "salary": "random_float",
            "revenue": "random_float",
            "quantity": "random_int",
            "count": "random_int",
            "age": "random_int",
            "score": "random_int",
            "rating": "random_int",
            "status": "word",
            "category": "word",
            "type": "word",
        }

        for key, method in name_map.items():
            if key in name:
                # Add sensible defaults for numeric methods
                if method == "random_float" and "price" in name or "amount" in name or "cost" in name:
                    return method  # args handled in generation
                return method

        # Type-based fallback
        type_map = {
            "integer": "random_int",
            "int": "random_int",
            "bigint": "random_int",
            "float": "random_float",
            "double": "random_float",
            "decimal": "random_float",
            "boolean": "boolean",
            "bool": "boolean",
            "date": "date_between",
            "timestamp": "date_time_between",
            "datetime": "date_time_between",
            "uuid": "uuid4",
            "text": "paragraph",
        }

        return type_map.get(dtype, "word")

    def _topological_sort(self, tables: list[TablePlan]) -> list[str]:
        """Sort tables by FK dependencies so parent tables are generated first."""
        graph = {t.name: set(t.depends_on) for t in tables}
        table_names = [t.name for t in tables]
        result = []
        visited = set()
        temp_mark = set()

        def visit(node):
            if node in temp_mark:
                # Circular dependency — just add it
                return
            if node in visited:
                return
            temp_mark.add(node)
            for dep in graph.get(node, set()):
                if dep in graph:
                    visit(dep)
            temp_mark.discard(node)
            visited.add(node)
            result.append(node)

        for name in table_names:
            visit(name)

        return result

    # ------------------------------------------------------------------
    # Data Generation
    # ------------------------------------------------------------------

    def generate_data(self, job_id: str, plan: GenerationPlan, tables: list[dict],
                      seed: int = None, locale: str = "en_US"):
        """
        Execute the generation plan — create tables in DuckDB and fill with synthetic data.
        Updates job progress in SQLite as it goes.
        """
        fake = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        # Track generated PKs for FK lookups
        pk_store: dict[str, list] = {}  # "table.column" -> list of generated PK values

        total_tables = len(plan.generation_order)
        total_rows_generated = 0

        # Create DuckDB tables
        duckdb_path = duckdb_store.create_database(job_id, tables)
        db.update_job_status(
            job_id, "generating",
            duckdb_path=duckdb_path,
            table_count=total_tables,
        )

        # Build lookup: table_name -> TablePlan
        plan_map = {tp.name: tp for tp in plan.tables}

        for table_idx, table_name in enumerate(plan.generation_order):
            table_plan = plan_map.get(table_name)
            if not table_plan:
                continue

            logger.info(f"Generating {table_plan.row_count} rows for table '{table_name}'...")
            db.update_job_progress(
                job_id,
                rows_generated=total_rows_generated,
                tables_completed=table_idx,
                current_table=table_name,
            )

            # Generate in batches
            columns = [cp.name for cp in table_plan.columns]
            batch = []
            generated_pks = {}  # column_name -> set of generated PKs for this table

            for col in table_plan.columns:
                if col.is_primary_key or col.unique:
                    generated_pks[col.name] = set()

            for row_idx in range(table_plan.row_count):
                row = []
                for col in table_plan.columns:
                    value = self._generate_column_value(
                        fake, col, row_idx, pk_store, generated_pks
                    )
                    row.append(value)
                batch.append(row)

                if len(batch) >= DEFAULT_BATCH_SIZE:
                    duckdb_store.insert_batch(job_id, table_name, columns, batch)
                    total_rows_generated += len(batch)
                    batch = []

                    # Update progress periodically
                    db.update_job_progress(
                        job_id,
                        rows_generated=total_rows_generated,
                        tables_completed=table_idx,
                        current_table=table_name,
                    )

            # Insert remaining batch
            if batch:
                duckdb_store.insert_batch(job_id, table_name, columns, batch)
                total_rows_generated += len(batch)

            # Store PKs for FK references
            for col in table_plan.columns:
                if col.is_primary_key:
                    pk_key = f"{table_name}.{col.name}"
                    pk_store[pk_key] = list(generated_pks.get(col.name, set()))
                    logger.info(f"Stored {len(pk_store[pk_key])} PKs for {pk_key}")

            db.update_job_progress(
                job_id,
                rows_generated=total_rows_generated,
                tables_completed=table_idx + 1,
                current_table=None,
            )

        # Mark completed
        db.update_job_status(
            job_id, "completed",
            rows_generated=total_rows_generated,
            tables_completed=total_tables,
        )

        logger.info(f"Generation complete: {total_rows_generated} total rows across {total_tables} tables")

    def _generate_column_value(self, fake: Faker, col: ColumnPlan, row_idx: int,
                                pk_store: dict, generated_pks: dict) -> Any:
        """Generate a single column value based on the column plan."""
        # Handle nullable columns
        if col.nullable and col.null_probability > 0:
            if random.random() < col.null_probability:
                return None

        # Handle foreign keys — pick from parent table's generated PKs
        if col.is_foreign_key and col.fk_reference:
            ref_values = pk_store.get(col.fk_reference, [])
            if ref_values:
                return random.choice(ref_values)
            # If parent table not yet generated, generate a value normally
            logger.debug(f"No FK values for {col.fk_reference}, generating standalone value")

        # Handle primary keys
        if col.is_primary_key:
            if col.data_type in ("integer", "int", "bigint"):
                value = row_idx + 1
            else:
                value = str(uuid.uuid4())[:8]

            if col.name in generated_pks:
                generated_pks[col.name].add(value)
            return value

        # Handle unique columns
        if col.unique and col.name in generated_pks:
            max_attempts = 100
            for _ in range(max_attempts):
                value = self._call_faker(fake, col)
                if value not in generated_pks[col.name]:
                    generated_pks[col.name].add(value)
                    return value
            # Fallback: append index
            value = f"{self._call_faker(fake, col)}_{row_idx}"
            generated_pks[col.name].add(value)
            return value

        return self._call_faker(fake, col)

    def _call_faker(self, fake: Faker, col: ColumnPlan) -> Any:
        """Call the appropriate Faker method for a column."""
        method_name = col.faker_method
        args = col.faker_args or {}

        try:
            # Handle special methods with default args
            if method_name == "random_int":
                min_val = args.get("min", 1)
                max_val = args.get("max", 9999)
                return fake.random_int(min=min_val, max=max_val)

            elif method_name == "random_float":
                min_val = args.get("min", 0.01)
                max_val = args.get("max", 9999.99)
                digits = args.get("right_digits", 2)
                return round(random.uniform(min_val, max_val), digits)

            elif method_name == "date_between":
                start = args.get("start_date", "-5y")
                end = args.get("end_date", "today")
                return str(fake.date_between(start_date=start, end_date=end))

            elif method_name == "date_time_between":
                start = args.get("start_date", "-5y")
                end = args.get("end_date", "now")
                return str(fake.date_time_between(start_date=start, end_date=end))

            elif method_name == "boolean":
                return fake.boolean()

            elif method_name == "uuid4":
                return str(fake.uuid4())

            else:
                # Generic Faker method call
                faker_func = getattr(fake, method_name, None)
                if faker_func and callable(faker_func):
                    return faker_func()
                else:
                    logger.warning(f"Unknown Faker method '{method_name}', falling back to 'word'")
                    return fake.word()

        except Exception as e:
            logger.warning(f"Faker method '{method_name}' failed: {e}, using fallback")
            return fake.word()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

generation_engine = GenerationEngine()
