"""
DuckDB Store — manages synthetic data storage per generation job.
Each job gets its own DuckDB file for full data isolation.
"""
import logging
import duckdb
import json
import csv
import io
from pathlib import Path
from config import DUCKDB_DIR

logger = logging.getLogger(__name__)


class DuckDBStore:
    """Manages DuckDB databases for synthetic data storage."""

    def get_db_path(self, job_id: str) -> Path:
        """Get the DuckDB file path for a job."""
        return DUCKDB_DIR / f"job_{job_id}.duckdb"

    def create_database(self, job_id: str, tables: list[dict]) -> str:
        """
        Create a DuckDB database with the given table schemas.
        
        Args:
            job_id: The generation job ID
            tables: List of table definitions with columns
            
        Returns:
            Path to the created DuckDB file
        """
        db_path = self.get_db_path(job_id)
        conn = duckdb.connect(str(db_path))

        try:
            for table in tables:
                table_name = table["name"]
                columns = table["columns"]
                
                col_defs = []
                for col in columns:
                    col_sql = f'"{col["name"]}" {self._map_type(col["data_type"])}'
                    if col.get("primary_key"):
                        col_sql += " PRIMARY KEY"
                    if not col.get("nullable", True):
                        col_sql += " NOT NULL"
                    if col.get("unique") and not col.get("primary_key"):
                        col_sql += " UNIQUE"
                    col_defs.append(col_sql)

                ddl = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(col_defs)})'
                logger.info(f"Creating table: {ddl}")
                conn.execute(ddl)

            conn.close()
            logger.info(f"DuckDB database created at {db_path} with {len(tables)} tables")
            return str(db_path)

        except Exception as e:
            conn.close()
            # Clean up on failure
            if db_path.exists():
                db_path.unlink()
            raise RuntimeError(f"Failed to create DuckDB database: {e}") from e

    def insert_batch(self, job_id: str, table_name: str, columns: list[str], rows: list[list]):
        """
        Insert a batch of rows into a table.
        
        Args:
            job_id: The generation job ID
            table_name: Target table name
            columns: Column names
            rows: List of row value lists
        """
        if not rows:
            return

        db_path = self.get_db_path(job_id)
        conn = duckdb.connect(str(db_path))

        try:
            placeholders = ", ".join(["?" for _ in columns])
            col_names = ", ".join([f'"{c}"' for c in columns])
            sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
            conn.executemany(sql, rows)
            conn.close()
        except Exception as e:
            conn.close()
            raise RuntimeError(f"Failed to insert batch into {table_name}: {e}") from e

    def get_table_names(self, job_id: str) -> list[str]:
        """Get all table names in the job's DuckDB database."""
        db_path = self.get_db_path(job_id)
        if not db_path.exists():
            return []

        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
            conn.close()
            return [t[0] for t in tables]
        except Exception:
            conn.close()
            return []

    def get_table_columns(self, job_id: str, table_name: str) -> list[str]:
        """Get column names for a table."""
        db_path = self.get_db_path(job_id)
        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            cols = conn.execute(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = ? AND table_schema = 'main' ORDER BY ordinal_position",
                [table_name]
            ).fetchall()
            conn.close()
            return [c[0] for c in cols]
        except Exception:
            conn.close()
            return []

    def get_row_count(self, job_id: str, table_name: str) -> int:
        """Get the number of rows in a table."""
        db_path = self.get_db_path(job_id)
        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
            conn.close()
            return count
        except Exception:
            conn.close()
            return 0

    def preview_data(self, job_id: str, table_name: str, page: int = 1, page_size: int = 50) -> dict:
        """
        Get a paginated preview of generated data.
        
        Returns:
            Dict with columns, rows, total_rows, page info
        """
        db_path = self.get_db_path(job_id)
        if not db_path.exists():
            return {"columns": [], "rows": [], "total_rows": 0, "page": 1, "page_size": page_size, "total_pages": 0}

        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            total_rows = conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
            total_pages = max(1, (total_rows + page_size - 1) // page_size)
            offset = (page - 1) * page_size

            columns = self.get_table_columns(job_id, table_name)
            rows = conn.execute(
                f'SELECT * FROM "{table_name}" LIMIT ? OFFSET ?',
                [page_size, offset]
            ).fetchall()

            conn.close()

            # Convert to serializable format
            serialized_rows = []
            for row in rows:
                serialized_rows.append([str(v) if v is not None else None for v in row])

            return {
                "table_name": table_name,
                "columns": columns,
                "rows": serialized_rows,
                "total_rows": total_rows,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        except Exception as e:
            conn.close()
            logger.error(f"Failed to preview data: {e}")
            return {"columns": [], "rows": [], "total_rows": 0, "page": 1, "page_size": page_size, "total_pages": 0}

    def export_csv(self, job_id: str, table_name: str) -> str:
        """Export a table as CSV string."""
        db_path = self.get_db_path(job_id)
        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            columns = self.get_table_columns(job_id, table_name)
            rows = conn.execute(f'SELECT * FROM "{table_name}"').fetchall()
            conn.close()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([str(v) if v is not None else "" for v in row])

            return output.getvalue()
        except Exception as e:
            conn.close()
            raise RuntimeError(f"CSV export failed: {e}") from e

    def export_sql(self, job_id: str, table_name: str) -> str:
        """Export a table as SQL INSERT statements."""
        db_path = self.get_db_path(job_id)
        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            columns = self.get_table_columns(job_id, table_name)
            rows = conn.execute(f'SELECT * FROM "{table_name}"').fetchall()
            conn.close()

            col_names = ", ".join([f'"{c}"' for c in columns])
            statements = []

            for row in rows:
                values = []
                for v in row:
                    if v is None:
                        values.append("NULL")
                    elif isinstance(v, (int, float)):
                        values.append(str(v))
                    elif isinstance(v, bool):
                        values.append("TRUE" if v else "FALSE")
                    else:
                        escaped = str(v).replace("'", "''")
                        values.append(f"'{escaped}'")

                statements.append(f'INSERT INTO "{table_name}" ({col_names}) VALUES ({", ".join(values)});')

            return "\n".join(statements)
        except Exception as e:
            conn.close()
            raise RuntimeError(f"SQL export failed: {e}") from e

    def export_json(self, job_id: str, table_name: str) -> str:
        """Export a table as JSON array."""
        db_path = self.get_db_path(job_id)
        conn = duckdb.connect(str(db_path), read_only=True)
        try:
            columns = self.get_table_columns(job_id, table_name)
            rows = conn.execute(f'SELECT * FROM "{table_name}"').fetchall()
            conn.close()

            records = []
            for row in rows:
                record = {}
                for i, col in enumerate(columns):
                    val = row[i]
                    record[col] = str(val) if val is not None else None
                records.append(record)

            return json.dumps(records, indent=2)
        except Exception as e:
            conn.close()
            raise RuntimeError(f"JSON export failed: {e}") from e

    def delete_database(self, job_id: str):
        """Delete the DuckDB file for a job."""
        db_path = self.get_db_path(job_id)
        if db_path.exists():
            db_path.unlink()
            logger.info(f"Deleted DuckDB database: {db_path}")

    def _map_type(self, data_type: str) -> str:
        """Map schema data types to DuckDB types."""
        type_map = {
            "integer": "INTEGER",
            "int": "INTEGER",
            "bigint": "BIGINT",
            "float": "FLOAT",
            "double": "DOUBLE",
            "decimal": "DECIMAL(10,2)",
            "varchar": "VARCHAR",
            "string": "VARCHAR",
            "text": "TEXT",
            "boolean": "BOOLEAN",
            "bool": "BOOLEAN",
            "date": "DATE",
            "timestamp": "TIMESTAMP",
            "datetime": "TIMESTAMP",
            "uuid": "VARCHAR",
            "email": "VARCHAR",
            "phone": "VARCHAR",
            "url": "VARCHAR",
            "json": "VARCHAR",
        }
        return type_map.get(data_type.lower().strip(), "VARCHAR")


# Module-level singleton
duckdb_store = DuckDBStore()
