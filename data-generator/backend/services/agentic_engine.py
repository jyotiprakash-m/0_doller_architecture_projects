"""
Agentic Generation Engine using LangGraph.
Replaces the basic LLM calls in generation_engine.py with an agentic workflow using LangGraph and LangChain.
"""

from __future__ import annotations

import json
import logging
import re
import random
import uuid
import time
from typing import Any, Optional, TypedDict, Dict, List

from faker import Faker

# LangChain / LangGraph imports
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END

from config import LLM_MODEL, LLM_REQUEST_TIMEOUT, LLM_TEMPERATURE, OLLAMA_BASE_URL, DEFAULT_BATCH_SIZE
from services.duckdb_store import duckdb_store
from services import db
from services.generation_engine import (
    ColumnPlan, TablePlan, GenerationPlan, _extract_json,
    _DDL_PARSE_PROMPT, _SCHEMA_ANALYSIS_PROMPT
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LangGraph State Definitions
# ---------------------------------------------------------------------------

class ParseDDLState(TypedDict):
    ddl: str
    result: Optional[List[Dict]]
    error: Optional[str]

class SchemaPlanState(TypedDict):
    schema_desc: str
    parsed_analysis: Optional[List[Dict]]
    error: Optional[str]

# ---------------------------------------------------------------------------
# Agentic Engine
# ---------------------------------------------------------------------------

class AgenticGenerationEngine:
    """
    Agentic synthetic data generation engine using LangGraph orchestration.
    """

    def __init__(self) -> None:
        self._llm: Optional[Ollama] = None
        self._ddl_graph = self._build_ddl_graph()
        self._plan_graph = self._build_plan_graph()

    def _get_llm(self) -> Ollama:
        if self._llm is None:
            self._llm = Ollama(
                model=LLM_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=LLM_TEMPERATURE,
                timeout=LLM_REQUEST_TIMEOUT,
            )
        return self._llm

    # ------------------------------------------------------------------
    # Graph 1: Parse DDL
    # ------------------------------------------------------------------
    def _build_ddl_graph(self):
        builder = StateGraph(ParseDDLState)

        def call_llm_parse(state: ParseDDLState):
            llm = self._get_llm()
            prompt = _DDL_PARSE_PROMPT.format(ddl=state["ddl"])
            try:
                response = llm.invoke(prompt)
                parsed = _extract_json(response)
                
                if isinstance(parsed, list):
                    return {"result": parsed, "error": None}
                else:
                    return {"result": None, "error": "Parsed output is not a list"}
            except Exception as e:
                return {"result": None, "error": str(e)}

        builder.add_node("parse", call_llm_parse)
        builder.add_edge(START, "parse")
        builder.add_edge("parse", END)

        return builder.compile()

    def parse_ddl(self, ddl: str) -> list[dict]:
        """Parse SQL DDL via LangGraph workflow."""
        try:
            initial_state = {"ddl": ddl, "result": None, "error": None}
            res = self._ddl_graph.invoke(initial_state)

            if res.get("result"):
                return res["result"]
            
            logger.warning(f"Agentic DDL parsing failed, using fallback. Error: {res.get('error')}")
        except Exception as e:
            logger.warning(f"Agent graph failed: {e}")

        # Fallback
        return self._fallback_parse_ddl(ddl)

    # ------------------------------------------------------------------
    # Graph 2: Schema Analysis
    # ------------------------------------------------------------------
    def _build_plan_graph(self):
        builder = StateGraph(SchemaPlanState)

        def call_llm_plan(state: SchemaPlanState):
            llm = self._get_llm()
            prompt = _SCHEMA_ANALYSIS_PROMPT.format(schema=state["schema_desc"])
            try:
                response = llm.invoke(prompt)
                parsed = _extract_json(response)
                
                if isinstance(parsed, list):
                    return {"parsed_analysis": parsed, "error": None}
                else:
                    return {"parsed_analysis": None, "error": "Parsed output is not a list"}
            except Exception as e:
                return {"parsed_analysis": None, "error": str(e)}

        builder.add_node("analyze", call_llm_plan)
        builder.add_edge(START, "analyze")
        builder.add_edge("analyze", END)

        return builder.compile()

    def create_generation_plan(self, tables: list[dict], row_count: int) -> GenerationPlan:
        """Create generation plan using LangGraph orchestration."""
        column_plans_map = {}
        schema_desc = json.dumps(tables, indent=2)

        try:
            initial_state = {"schema_desc": schema_desc, "parsed_analysis": None, "error": None}
            res = self._plan_graph.invoke(initial_state)

            parsed = res.get("parsed_analysis")
            if parsed:
                for item in parsed:
                    key = f"{item.get('table_name', '')}.{item.get('column_name', '')}"
                    column_plans_map[key] = item
                logger.info(f"Agentic LLM analyzed {len(column_plans_map)} columns")
            else:
                logger.warning(f"Agentic analysis failed: {res.get('error')}")
        except Exception as e:
            logger.warning(f"Agentic plan graph failed, using heuristic: {e}")

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

                faker_method = llm_plan.get("faker_method") or self._infer_faker_method(col_def)
                faker_args = llm_plan.get("faker_args", {})
                null_prob = llm_plan.get("null_probability", 0.0)

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

        generation_order = self._topological_sort(table_plans)
        total_rows = row_count * len(table_plans)

        return GenerationPlan(
            tables=table_plans,
            generation_order=generation_order,
            total_rows=total_rows,
        )

    # ------------------------------------------------------------------
    # Heuristics & Helpers (mirrored from GenerationEngine)
    # ------------------------------------------------------------------

    def _fallback_parse_ddl(self, ddl: str) -> list[dict]:
        # Using exact same regex fallback logic
        tables = []
        table_pattern = re.compile(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?(\w+)[`"\']?\s*\((.*?)\);',
            re.IGNORECASE | re.DOTALL
        )

        for match in table_pattern.finditer(ddl):
            table_name = match.group(1)
            columns_str = match.group(2)
            columns = []

            for line in columns_str.split(","):
                line = line.strip()
                if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "INDEX", "CONSTRAINT", "CHECK")):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                col_name = parts[0].strip('`"\'')
                col_type = parts[1].strip('`"\'').lower()

                type_map = {
                    "int": "integer", "serial": "integer", "bigserial": "bigint",
                    "varchar": "varchar", "char": "varchar", "character": "varchar",
                    "text": "text", "bool": "boolean", "float4": "float",
                    "float8": "double", "numeric": "float", "real": "float",
                    "datetime": "timestamp", "timestamptz": "timestamp",
                }
                base_type = re.sub(r'\(.*?\)', '', col_type)
                col_type = type_map.get(base_type, base_type)

                line_upper = line.upper()
                is_pk = "PRIMARY KEY" in line_upper
                is_unique = "UNIQUE" in line_upper
                is_not_null = "NOT NULL" in line_upper

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

    def _infer_faker_method(self, col_def: dict) -> str:
        name = col_def.get("name", "").lower()
        dtype = col_def.get("data_type", "").lower()

        name_map = {
            "email": "email", "mail": "email", "first_name": "first_name",
            "firstname": "first_name", "last_name": "last_name", "lastname": "last_name",
            "name": "name", "full_name": "name", "username": "user_name",
            "user_name": "user_name", "phone": "phone_number", "telephone": "phone_number",
            "mobile": "phone_number", "address": "address", "street": "street_address",
            "city": "city", "state": "state", "country": "country", "zip": "zipcode",
            "zipcode": "zipcode", "postal_code": "zipcode", "company": "company",
            "organization": "company", "job": "job", "title": "job", "job_title": "job",
            "url": "url", "website": "url", "ip": "ipv4", "ip_address": "ipv4",
            "password": "password", "description": "paragraph", "bio": "paragraph",
            "about": "paragraph", "comment": "sentence", "note": "sentence",
            "notes": "paragraph", "color": "color_name", "price": "random_float",
            "amount": "random_float", "cost": "random_float", "salary": "random_float",
            "revenue": "random_float", "quantity": "random_int", "count": "random_int",
            "age": "random_int", "score": "random_int", "rating": "random_int",
            "status": "word", "category": "word", "type": "word",
        }

        for key, method in name_map.items():
            if key in name:
                if method == "random_float" and ("price" in name or "amount" in name or "cost" in name):
                    return method
                return method

        type_map = {
            "integer": "random_int", "int": "random_int", "bigint": "random_int",
            "float": "random_float", "double": "random_float", "decimal": "random_float",
            "boolean": "boolean", "bool": "boolean", "date": "date_between",
            "timestamp": "date_time_between", "datetime": "date_time_between",
            "uuid": "uuid4", "text": "paragraph",
        }

        return type_map.get(dtype, "word")

    def _topological_sort(self, tables: list[TablePlan]) -> list[str]:
        graph = {t.name: set(t.depends_on) for t in tables}
        table_names = [t.name for t in tables]
        result = []
        visited = set()
        temp_mark = set()

        def visit(node):
            if node in temp_mark: return
            if node in visited: return
            temp_mark.add(node)
            for dep in graph.get(node, set()):
                if dep in graph: visit(dep)
            temp_mark.discard(node)
            visited.add(node)
            result.append(node)

        for name in table_names:
            visit(name)

        return result

    # ------------------------------------------------------------------
    # Data Generation (Direct Execution)
    # ------------------------------------------------------------------

    def generate_data(self, job_id: str, plan: GenerationPlan, tables: list[dict],
                      seed: int = None, locale: str = "en_US"):
        fake = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        pk_store: dict[str, list] = {}

        total_tables = len(plan.generation_order)
        total_rows_generated = 0

        duckdb_path = duckdb_store.create_database(job_id, tables)
        db.update_job_status(
            job_id, "generating", duckdb_path=duckdb_path, table_count=total_tables,
        )

        plan_map = {tp.name: tp for tp in plan.tables}

        for table_idx, table_name in enumerate(plan.generation_order):
            table_plan = plan_map.get(table_name)
            if not table_plan:
                continue

            logger.info(f"Generating {table_plan.row_count} rows for table '{table_name}'...")
            db.update_job_progress(
                job_id, rows_generated=total_rows_generated,
                tables_completed=table_idx, current_table=table_name,
            )

            columns = [cp.name for cp in table_plan.columns]
            batch = []
            generated_pks = {col.name: set() for col in table_plan.columns if col.is_primary_key or col.unique}

            for row_idx in range(table_plan.row_count):
                row = []
                for col in table_plan.columns:
                    value = self._generate_column_value(fake, col, row_idx, pk_store, generated_pks)
                    row.append(value)
                batch.append(row)

                if len(batch) >= DEFAULT_BATCH_SIZE:
                    duckdb_store.insert_batch(job_id, table_name, columns, batch)
                    total_rows_generated += len(batch)
                    batch = []
                    db.update_job_progress(
                        job_id, rows_generated=total_rows_generated,
                        tables_completed=table_idx, current_table=table_name,
                    )

            if batch:
                duckdb_store.insert_batch(job_id, table_name, columns, batch)
                total_rows_generated += len(batch)

            for col in table_plan.columns:
                if col.is_primary_key:
                    pk_key = f"{table_name}.{col.name}"
                    pk_store[pk_key] = list(generated_pks.get(col.name, set()))

            db.update_job_progress(
                job_id, rows_generated=total_rows_generated,
                tables_completed=table_idx + 1, current_table=None,
            )

        db.update_job_status(
            job_id, "completed",
            rows_generated=total_rows_generated,
            tables_completed=total_tables,
        )
        logger.info(f"Agentic generation complete: {total_rows_generated} rows")

    def _generate_column_value(self, fake: Faker, col: ColumnPlan, row_idx: int,
                                pk_store: dict, generated_pks: dict) -> Any:
        if col.nullable and col.null_probability > 0:
            if random.random() < col.null_probability:
                return None

        if col.is_foreign_key and col.fk_reference:
            ref_values = pk_store.get(col.fk_reference, [])
            if ref_values: return random.choice(ref_values)

        if col.is_primary_key:
            value = row_idx + 1 if col.data_type in ("integer", "int", "bigint") else str(uuid.uuid4())[:8]
            if col.name in generated_pks: generated_pks[col.name].add(value)
            return value

        if col.unique and col.name in generated_pks:
            for _ in range(100):
                value = self._call_faker(fake, col)
                if value not in generated_pks[col.name]:
                    generated_pks[col.name].add(value)
                    return value
            value = f"{self._call_faker(fake, col)}_{row_idx}"
            generated_pks[col.name].add(value)
            return value

        return self._call_faker(fake, col)

    def _call_faker(self, fake: Faker, col: ColumnPlan) -> Any:
        method_name = col.faker_method
        args = col.faker_args or {}

        try:
            if method_name == "random_int":
                return fake.random_int(min=args.get("min", 1), max=args.get("max", 9999))
            elif method_name == "random_float":
                return round(random.uniform(args.get("min", 0.01), args.get("max", 9999.99)), args.get("right_digits", 2))
            elif method_name == "date_between":
                return str(fake.date_between(start_date=args.get("start_date", "-5y"), end_date=args.get("end_date", "today")))
            elif method_name == "date_time_between":
                return str(fake.date_time_between(start_date=args.get("start_date", "-5y"), end_date=args.get("end_date", "now")))
            elif method_name == "boolean":
                return fake.boolean()
            elif method_name == "uuid4":
                return str(fake.uuid4())
            else:
                faker_func = getattr(fake, method_name, None)
                if faker_func and callable(faker_func):
                    return faker_func()
                return fake.word()
        except:
            return fake.word()

agentic_generation_engine = AgenticGenerationEngine()
