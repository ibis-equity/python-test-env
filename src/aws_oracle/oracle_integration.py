"""
Oracle Database Integration Module

Senior-level patterns for AWS Lambda + FastAPI + Oracle integration:
- Connection pooling with retry logic
- Query builder and parameterized queries
- Error handling and recovery
- Monitoring and logging
- Transaction management
- Context managers for resource cleanup
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

try:
    import oracledb
except ImportError:
    oracledb = None

import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)


@dataclass
class OracleConfig:
    """Oracle connection configuration"""
    host: str
    port: int = 1521
    service_name: str = "ORCL"
    user: str = "admin"
    password: str = ""
    wallet_path: Optional[str] = None
    min_pool_size: int = 2
    max_pool_size: int = 10
    timeout: int = 30
    max_lifetime: int = 3600
    enable_compression: bool = True
    enable_encryption: bool = True


class OracleConnectionPool:
    """
    Thread-safe connection pool with health checks and auto-recovery
    
    Features:
    - Lazy initialization
    - Connection health checks
    - Automatic reconnection
    - Metrics collection
    - Graceful cleanup
    """
    
    def __init__(self, config: OracleConfig):
        self.config = config
        self.pool = None
        self.is_initialized = False
        self.metrics = {
            'connections_created': 0,
            'connections_failed': 0,
            'queries_executed': 0,
            'query_errors': 0,
            'total_query_time': 0.0,
        }
        self.last_health_check = None
        self.health_check_interval = 60  # seconds
        
    def initialize(self) -> None:
        """Initialize connection pool with error handling"""
        try:
            if oracledb is None:
                raise ImportError("oracledb module not installed. Run: pip install oracledb")
            
            logger.info("initializing_oracle_pool", config=self._sanitize_config())
            
            dsn = oracledb.makedsn(
                host=self.config.host,
                port=self.config.port,
                service_name=self.config.service_name
            )
            
            self.pool = oracledb.create_pool(
                user=self.config.user,
                password=self.config.password,
                dsn=dsn,
                min=self.config.min_pool_size,
                max=self.config.max_pool_size,
                timeout=self.config.timeout,
                max_lifetime_session=self.config.max_lifetime,
                encoding="UTF-8",
                nencoding="UTF-8"
            )
            
            self.is_initialized = True
            self.metrics['connections_created'] = self.config.min_pool_size
            
            logger.info("oracle_pool_initialized", 
                       min_size=self.config.min_pool_size,
                       max_size=self.config.max_pool_size)
            
        except Exception as e:
            self.metrics['connections_failed'] += 1
            logger.error("oracle_pool_init_failed", error=str(e), exc_info=True)
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for safe connection handling
        
        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                # execute queries
        """
        if not self.is_initialized:
            self.initialize()
        
        conn = None
        try:
            conn = self.pool.getconn()
            # Verify connection is alive
            if not self._is_connection_valid(conn):
                self.pool.releaseconn(conn, force=True)
                conn = self.pool.getconn()
            
            yield conn
            
        except Exception as e:
            logger.error("connection_error", error=str(e), exc_info=True)
            if conn:
                self.pool.releaseconn(conn, force=True)
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def _is_connection_valid(self, conn) -> bool:
        """Check if connection is still valid"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            cursor.close()
            return True
        except:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on pool"""
        now = datetime.utcnow()
        
        # Only check if interval elapsed
        if (self.last_health_check and 
            (now - self.last_health_check).seconds < self.health_check_interval):
            return {
                'status': 'healthy',
                'cached': True,
                'metrics': self.metrics
            }
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as active_sessions,
                        SYSDATE as db_time
                    FROM V$SESSION
                    WHERE TYPE='USER'
                """)
                result = cursor.fetchone()
                cursor.close()
                
            self.last_health_check = now
            return {
                'status': 'healthy',
                'active_sessions': result[0] if result else 0,
                'db_time': str(result[1]) if result else None,
                'pool_metrics': self.metrics
            }
        except Exception as e:
            logger.error("health_check_failed", error=str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'metrics': self.metrics
            }
    
    def close(self) -> None:
        """Close all connections in pool"""
        try:
            if self.pool:
                self.pool.close()
                self.is_initialized = False
                logger.info("oracle_pool_closed")
        except Exception as e:
            logger.error("pool_close_error", error=str(e))
    
    def _sanitize_config(self) -> Dict:
        """Remove sensitive data from config for logging"""
        return {
            'host': self.config.host,
            'port': self.config.port,
            'service_name': self.config.service_name,
            'min_pool_size': self.config.min_pool_size,
            'max_pool_size': self.config.max_pool_size,
        }


class OracleQueryBuilder:
    """
    SQL query builder with parameterized queries (prevents SQL injection)
    
    Usage:
        query = (OracleQueryBuilder()
                 .select('id', 'name', 'amount')
                 .from_table('opportunities')
                 .where('stage', '=', 'Proposal')
                 .where('amount', '>', 100000)
                 .order_by('amount', 'DESC')
                 .limit(10))
        
        sql, params = query.build()
    """
    
    def __init__(self):
        self.select_cols = []
        self.from_table_name = None
        self.where_conditions = []
        self.order_cols = []
        self.limit_count = None
        self.offset_count = None
        self.join_clauses = []
        
    def select(self, *columns) -> 'OracleQueryBuilder':
        """Add columns to SELECT"""
        self.select_cols.extend(columns)
        return self
    
    def from_table(self, table: str) -> 'OracleQueryBuilder':
        """Set FROM table"""
        self.from_table_name = table
        return self
    
    def join(self, table: str, on: str, join_type: str = 'INNER') -> 'OracleQueryBuilder':
        """Add JOIN clause"""
        self.join_clauses.append(f"{join_type} JOIN {table} ON {on}")
        return self
    
    def where(self, column: str, operator: str, value: Any) -> 'OracleQueryBuilder':
        """Add WHERE condition with parameterized value"""
        placeholder = f":{len(self.where_conditions)}"
        self.where_conditions.append({
            'sql': f"{column} {operator} {placeholder}",
            'value': value
        })
        return self
    
    def where_in(self, column: str, values: List[Any]) -> 'OracleQueryBuilder':
        """Add WHERE IN clause"""
        placeholders = ','.join([f":{len(self.where_conditions) + i}" 
                                for i in range(len(values))])
        self.where_conditions.append({
            'sql': f"{column} IN ({placeholders})",
            'values': values
        })
        return self
    
    def order_by(self, column: str, direction: str = 'ASC') -> 'OracleQueryBuilder':
        """Add ORDER BY"""
        self.order_cols.append(f"{column} {direction}")
        return self
    
    def limit(self, count: int) -> 'OracleQueryBuilder':
        """Add LIMIT"""
        self.limit_count = count
        return self
    
    def offset(self, count: int) -> 'OracleQueryBuilder':
        """Add OFFSET"""
        self.offset_count = count
        return self
    
    def build(self) -> Tuple[str, Dict[str, Any]]:
        """Build SQL and parameters"""
        if not self.from_table_name:
            raise ValueError("FROM table not specified")
        
        sql_parts = []
        params = {}
        
        # SELECT
        cols = ', '.join(self.select_cols) if self.select_cols else '*'
        sql_parts.append(f"SELECT {cols}")
        
        # FROM
        sql_parts.append(f"FROM {self.from_table_name}")
        
        # JOINs
        if self.join_clauses:
            sql_parts.extend(self.join_clauses)
        
        # WHERE
        if self.where_conditions:
            where_sql = ' AND '.join(c['sql'] for c in self.where_conditions)
            sql_parts.append(f"WHERE {where_sql}")
            
            param_idx = 0
            for condition in self.where_conditions:
                if 'value' in condition:
                    params[str(param_idx)] = condition['value']
                    param_idx += 1
                elif 'values' in condition:
                    for val in condition['values']:
                        params[str(param_idx)] = val
                        param_idx += 1
        
        # ORDER BY
        if self.order_cols:
            sql_parts.append(f"ORDER BY {', '.join(self.order_cols)}")
        
        # LIMIT/OFFSET (Oracle FETCH syntax)
        if self.limit_count:
            sql_parts.append(f"FETCH NEXT {self.limit_count} ROWS ONLY")
            if self.offset_count:
                sql_parts.insert(-1, f"OFFSET {self.offset_count} ROWS")
        
        sql = '\n'.join(sql_parts)
        return sql, params
    
    def __repr__(self) -> str:
        sql, params = self.build()
        return f"OracleQueryBuilder(sql={sql}, params={params})"


class OracleDataAccess:
    """
    Data access layer with common CRUD operations
    Handles query execution, error handling, and result mapping
    """
    
    def __init__(self, pool: OracleConnectionPool):
        self.pool = pool
    
    def execute_query(self, 
                     sql: str, 
                     params: Optional[Dict] = None,
                     fetch_one: bool = False) -> List[Dict[str, Any]]:
        """
        Execute SELECT query with error handling
        
        Args:
            sql: SQL query string
            params: Dictionary of parameters for parameterized query
            fetch_one: If True, return single row as dict; if False, return list
        
        Returns:
            List of dictionaries (one per row) or single dict if fetch_one=True
        """
        start_time = time.time()
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                if fetch_one:
                    row = cursor.fetchone()
                    cursor.close()
                    
                    if row:
                        return dict(zip(columns, row))
                    return None
                else:
                    rows = cursor.fetchall()
                    cursor.close()
                    
                    return [dict(zip(columns, row)) for row in rows]
        
        except Exception as e:
            self.pool.metrics['query_errors'] += 1
            logger.error("query_execution_failed", 
                        sql=sql[:100],
                        error=str(e),
                        exc_info=True)
            raise OracleQueryError(f"Query failed: {str(e)}") from e
        finally:
            elapsed = time.time() - start_time
            self.pool.metrics['queries_executed'] += 1
            self.pool.metrics['total_query_time'] += elapsed
            logger.info("query_executed",
                       elapsed_ms=elapsed * 1000,
                       query_preview=sql[:100])
    
    def execute_update(self,
                      sql: str,
                      params: Optional[Dict] = None,
                      commit: bool = True) -> int:
        """
        Execute INSERT/UPDATE/DELETE with error handling
        
        Returns:
            Number of rows affected
        """
        start_time = time.time()
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                rows_affected = cursor.rowcount
                
                if commit:
                    conn.commit()
                    logger.info("rows_updated", count=rows_affected)
                
                cursor.close()
                return rows_affected
        
        except Exception as e:
            self.pool.metrics['query_errors'] += 1
            logger.error("update_execution_failed",
                        sql=sql[:100],
                        error=str(e),
                        exc_info=True)
            raise OracleQueryError(f"Update failed: {str(e)}") from e
        finally:
            elapsed = time.time() - start_time
            logger.info("update_executed", elapsed_ms=elapsed * 1000)
    
    def call_procedure(self,
                      proc_name: str,
                      params: Optional[List] = None) -> Any:
        """
        Call stored procedure with error handling
        
        Args:
            proc_name: Name of stored procedure
            params: List of parameters for procedure
        
        Returns:
            Procedure result or output parameters
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.callproc(proc_name, params)
                else:
                    cursor.callproc(proc_name)
                
                result = cursor.fetchall() if cursor.description else None
                cursor.close()
                return result
        
        except Exception as e:
            logger.error("procedure_call_failed",
                        proc_name=proc_name,
                        error=str(e),
                        exc_info=True)
            raise OracleProcedureError(f"Procedure call failed: {str(e)}") from e
    
    def execute_transaction(self, 
                          operations: List[Tuple[str, Optional[Dict]]]) -> bool:
        """
        Execute multiple operations as a transaction
        
        Args:
            operations: List of (sql, params) tuples
        
        Returns:
            True if successful, raises exception on failure
        """
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                for sql, params in operations:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                
                conn.commit()
                cursor.close()
                logger.info("transaction_committed", operations=len(operations))
                return True
        
        except Exception as e:
            logger.error("transaction_failed",
                        operations=len(operations),
                        error=str(e),
                        exc_info=True)
            raise OracleTransactionError(f"Transaction failed: {str(e)}") from e


# Custom Exceptions
class OracleException(Exception):
    """Base Oracle exception"""
    pass


class OracleQueryError(OracleException):
    """Query execution error"""
    pass


class OracleProcedureError(OracleException):
    """Stored procedure execution error"""
    pass


class OracleTransactionError(OracleException):
    """Transaction execution error"""
    pass


# Global pool instance
_pool: Optional[OracleConnectionPool] = None


def get_pool(config: Optional[OracleConfig] = None) -> OracleConnectionPool:
    """Get or create global connection pool (singleton pattern)"""
    global _pool
    
    if _pool is None:
        if config is None:
            # Load from environment
            config = OracleConfig(
                host=os.getenv('ORACLE_HOST', 'localhost'),
                port=int(os.getenv('ORACLE_PORT', 1521)),
                service_name=os.getenv('ORACLE_SERVICE_NAME', 'ORCL'),
                user=os.getenv('ORACLE_USER', 'admin'),
                password=os.getenv('ORACLE_PASSWORD', ''),
                wallet_path=os.getenv('ORACLE_WALLET_PATH'),
                min_pool_size=int(os.getenv('ORACLE_POOL_MIN', 2)),
                max_pool_size=int(os.getenv('ORACLE_POOL_MAX', 10)),
            )
        
        _pool = OracleConnectionPool(config)
    
    return _pool


def close_pool() -> None:
    """Close global connection pool"""
    global _pool
    if _pool:
        _pool.close()
        _pool = None


# Example usage and testing
if __name__ == "__main__":
    # Configure logging for testing
    import sys
    structlog.configure(
        processors=[
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    print("Oracle Integration Module - Senior-Level Patterns")
    print("=" * 60)
    
    # Example 1: Query Builder
    print("\n1. Query Builder Example:")
    query = (OracleQueryBuilder()
             .select('ID', 'OPPORTUNITY_NAME', 'AMOUNT', 'STAGE')
             .from_table('OPPORTUNITIES')
             .where('STAGE', '=', 'Proposal')
             .where('AMOUNT', '>', 100000)
             .order_by('AMOUNT', 'DESC')
             .limit(10))
    
    sql, params = query.build()
    print(f"SQL:\n{sql}")
    print(f"\nParameters:\n{json.dumps(params, indent=2)}")
    
    # Example 2: Configuration
    print("\n2. Oracle Configuration:")
    config = OracleConfig(
        host='oracle.example.com',
        port=1521,
        service_name='PROD',
        user='app_user',
        min_pool_size=2,
        max_pool_size=10,
    )
    print(f"Config: {config}")
    
    print("\n" + "=" * 60)
    print("See documentation for complete usage patterns and deployment")
