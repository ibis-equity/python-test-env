"""
Repository/Data Access Layer for Oracle

Senior-level patterns for data access abstraction:
- Repository pattern for each entity
- Query building with filters
- Pagination support
- Error handling and retry logic
- Transaction management
- Performance optimization (batching, indexes)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging
from abc import ABC, abstractmethod

from .oracle_integration import (
    OracleDataAccess, OracleQueryBuilder, OracleConnectionPool,
    OracleException, OracleQueryError, OracleTransactionError
)
from .oracle_models import (
    Account, AccountCreate, AccountUpdate,
    Contact, ContactCreate, ContactUpdate,
    Opportunity, OpportunityCreate, OpportunityUpdate,
    OpportunitySummary, OpportunityFilter, OpportunityStage,
    Activity, ActivityCreate, BatchOpportunityCreate,
    BatchOperationResult
)

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Abstract base repository for common CRUD operations"""
    
    def __init__(self, data_access: OracleDataAccess):
        self.da = data_access
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Dict]:
        """Get single record by ID"""
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all records with pagination"""
        pass
    
    @abstractmethod
    def create(self, obj: Any) -> Dict:
        """Create new record"""
        pass
    
    @abstractmethod
    def update(self, id: int, obj: Any) -> bool:
        """Update existing record"""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete record"""
        pass


class AccountRepository(BaseRepository):
    """Repository for Account operations"""
    
    TABLE = "ACCOUNTS"
    COLUMNS = [
        "ID", "NAME", "INDUSTRY", "ACCOUNT_TYPE", "PHONE", "WEBSITE",
        "EMPLOYEE_COUNT", "ANNUAL_REVENUE", "STATUS",
        "CREATED_DATE", "MODIFIED_DATE", "CREATED_BY", "MODIFIED_BY"
    ]
    
    def get_by_id(self, id: int) -> Optional[Account]:
        """Get account by ID"""
        try:
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("ID", "=", id))
            
            sql, params = query.build()
            result = self.da.execute_query(sql, params, fetch_one=True)
            
            if result:
                return Account(**result)
            return None
        
        except Exception as e:
            logger.error(f"Failed to get account {id}: {str(e)}")
            raise
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Account]:
        """Get all accounts with pagination"""
        try:
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .order_by("CREATED_DATE", "DESC")
                    .limit(limit)
                    .offset(offset))
            
            sql, params = query.build()
            results = self.da.execute_query(sql, params)
            
            return [Account(**r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to get all accounts: {str(e)}")
            raise
    
    def get_by_status(self, status: str, limit: int = 100) -> List[Account]:
        """Get accounts by status"""
        try:
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("STATUS", "=", status)
                    .order_by("NAME")
                    .limit(limit))
            
            sql, params = query.build()
            results = self.da.execute_query(sql, params)
            
            return [Account(**r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to get accounts by status: {str(e)}")
            raise
    
    def get_by_industry(self, industry: str, limit: int = 100) -> List[Account]:
        """Get accounts by industry"""
        try:
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("INDUSTRY", "=", industry)
                    .order_by("ANNUAL_REVENUE", "DESC")
                    .limit(limit))
            
            sql, params = query.build()
            results = self.da.execute_query(sql, params)
            
            return [Account(**r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to get accounts by industry: {str(e)}")
            raise
    
    def create(self, account: AccountCreate, created_by: str) -> Account:
        """Create new account"""
        try:
            sql = f"""
            INSERT INTO {self.TABLE} 
            (NAME, INDUSTRY, ACCOUNT_TYPE, PHONE, WEBSITE, 
             EMPLOYEE_COUNT, ANNUAL_REVENUE, STATUS, CREATED_DATE, CREATED_BY)
            VALUES (:0, :1, :2, :3, :4, :5, :6, :7, SYSTIMESTAMP, :8)
            """
            
            params = {
                '0': account.name,
                '1': account.industry,
                '2': account.account_type,
                '3': account.phone,
                '4': account.website,
                '5': account.employee_count,
                '6': account.annual_revenue,
                '7': account.status,
                '8': created_by,
            }
            
            self.da.execute_update(sql, params, commit=True)
            
            # Retrieve created account
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("NAME", "=", account.name)
                    .order_by("CREATED_DATE", "DESC"))
            
            sql, qparams = query.build()
            result = self.da.execute_query(sql, qparams, fetch_one=True)
            
            logger.info(f"Created account: {result['ID']}")
            return Account(**result)
        
        except Exception as e:
            logger.error(f"Failed to create account: {str(e)}")
            raise
    
    def update(self, id: int, update: AccountUpdate, modified_by: str) -> bool:
        """Update account"""
        try:
            # Build dynamic UPDATE based on provided fields
            updates = []
            params = {}
            param_idx = 0
            
            if update.name:
                updates.append(f"NAME = :{param_idx}")
                params[str(param_idx)] = update.name
                param_idx += 1
            
            if update.industry:
                updates.append(f"INDUSTRY = :{param_idx}")
                params[str(param_idx)] = update.industry
                param_idx += 1
            
            if update.account_type:
                updates.append(f"ACCOUNT_TYPE = :{param_idx}")
                params[str(param_idx)] = update.account_type
                param_idx += 1
            
            if update.phone:
                updates.append(f"PHONE = :{param_idx}")
                params[str(param_idx)] = update.phone
                param_idx += 1
            
            if update.annual_revenue is not None:
                updates.append(f"ANNUAL_REVENUE = :{param_idx}")
                params[str(param_idx)] = update.annual_revenue
                param_idx += 1
            
            if update.status:
                updates.append(f"STATUS = :{param_idx}")
                params[str(param_idx)] = update.status
                param_idx += 1
            
            if not updates:
                return False
            
            updates.append(f"MODIFIED_DATE = SYSTIMESTAMP")
            updates.append(f"MODIFIED_BY = :{param_idx}")
            params[str(param_idx)] = modified_by
            
            sql = f"UPDATE {self.TABLE} SET {', '.join(updates)} WHERE ID = :{param_idx + 1}"
            params[str(param_idx + 1)] = id
            
            rows_affected = self.da.execute_update(sql, params, commit=True)
            logger.info(f"Updated account {id}: {rows_affected} rows affected")
            
            return rows_affected > 0
        
        except Exception as e:
            logger.error(f"Failed to update account {id}: {str(e)}")
            raise
    
    def delete(self, id: int) -> bool:
        """Delete account (soft delete by status)"""
        try:
            sql = f"UPDATE {self.TABLE} SET STATUS = 'Inactive', MODIFIED_DATE = SYSTIMESTAMP WHERE ID = :0"
            params = {'0': id}
            
            rows_affected = self.da.execute_update(sql, params, commit=True)
            logger.info(f"Deleted account {id}: {rows_affected} rows affected")
            
            return rows_affected > 0
        
        except Exception as e:
            logger.error(f"Failed to delete account {id}: {str(e)}")
            raise


class OpportunityRepository(BaseRepository):
    """Repository for Opportunity operations"""
    
    TABLE = "OPPORTUNITIES"
    COLUMNS = [
        "ID", "NAME", "ACCOUNT_ID", "AMOUNT", "CURRENCY", "STAGE",
        "PROBABILITY", "CLOSE_DATE", "DESCRIPTION", "PRIMARY_CONTACT_ID",
        "STATUS", "FISCAL_QUARTER", "FORECAST_CATEGORY",
        "CREATED_DATE", "MODIFIED_DATE", "CREATED_BY", "MODIFIED_BY"
    ]
    
    def __init__(self, data_access: OracleDataAccess, account_repo: AccountRepository):
        super().__init__(data_access)
        self.account_repo = account_repo
    
    def get_by_id(self, id: int) -> Optional[Opportunity]:
        """Get opportunity by ID"""
        try:
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("ID", "=", id))
            
            sql, params = query.build()
            result = self.da.execute_query(sql, params, fetch_one=True)
            
            if result:
                return Opportunity(**result)
            return None
        
        except Exception as e:
            logger.error(f"Failed to get opportunity {id}: {str(e)}")
            raise
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Opportunity]:
        """Get all opportunities"""
        try:
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("STATUS", "=", "Active")
                    .order_by("CLOSE_DATE")
                    .limit(limit)
                    .offset(offset))
            
            sql, params = query.build()
            results = self.da.execute_query(sql, params)
            
            return [Opportunity(**r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to get all opportunities: {str(e)}")
            raise
    
    def get_by_account(self, account_id: int) -> List[Opportunity]:
        """Get opportunities for account"""
        try:
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("ACCOUNT_ID", "=", account_id)
                    .where("STATUS", "=", "Active")
                    .order_by("CLOSE_DATE"))
            
            sql, params = query.build()
            results = self.da.execute_query(sql, params)
            
            return [Opportunity(**r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to get opportunities for account {account_id}: {str(e)}")
            raise
    
    def get_by_stage(self, stage: OpportunityStage) -> List[Opportunity]:
        """Get opportunities by stage"""
        try:
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("STAGE", "=", stage)
                    .where("STATUS", "=", "Active")
                    .order_by("PROBABILITY", "DESC")
                    .order_by("AMOUNT", "DESC"))
            
            sql, params = query.build()
            results = self.da.execute_query(sql, params)
            
            return [Opportunity(**r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to get opportunities by stage {stage}: {str(e)}")
            raise
    
    def filter(self, filter_query: OpportunityFilter) -> List[Opportunity]:
        """Filter opportunities by multiple criteria"""
        try:
            query = OracleQueryBuilder().select(*self.COLUMNS).from_table(self.TABLE)
            query = query.where("STATUS", "=", "Active")
            
            if filter_query.stage:
                query = query.where("STAGE", "=", filter_query.stage)
            
            if filter_query.min_amount:
                query = query.where("AMOUNT", ">=", filter_query.min_amount)
            
            if filter_query.max_amount:
                query = query.where("AMOUNT", "<=", filter_query.max_amount)
            
            if filter_query.min_probability is not None:
                query = query.where("PROBABILITY", ">=", filter_query.min_probability)
            
            if filter_query.max_probability is not None:
                query = query.where("PROBABILITY", "<=", filter_query.max_probability)
            
            if filter_query.account_id:
                query = query.where("ACCOUNT_ID", "=", filter_query.account_id)
            
            if filter_query.close_date_from:
                query = query.where("CLOSE_DATE", ">=", filter_query.close_date_from)
            
            if filter_query.close_date_to:
                query = query.where("CLOSE_DATE", "<=", filter_query.close_date_to)
            
            query = query.order_by("AMOUNT", "DESC").limit(filter_query.limit).offset(filter_query.offset)
            
            sql, params = query.build()
            results = self.da.execute_query(sql, params)
            
            return [Opportunity(**r) for r in results]
        
        except Exception as e:
            logger.error(f"Failed to filter opportunities: {str(e)}")
            raise
    
    def get_summary(self) -> OpportunitySummary:
        """Get opportunity pipeline summary"""
        try:
            sql = """
            SELECT 
                COUNT(*) as total_opportunities,
                SUM(AMOUNT) as total_value,
                AVG(AMOUNT) as avg_amount,
                COUNT(CASE WHEN STAGE = 'Qualification' THEN 1 END) as qual_count,
                SUM(CASE WHEN STAGE = 'Qualification' THEN AMOUNT ELSE 0 END) as qual_value,
                COUNT(CASE WHEN STAGE = 'Proposal' THEN 1 END) as prop_count,
                SUM(CASE WHEN STAGE = 'Proposal' THEN AMOUNT ELSE 0 END) as prop_value,
                COUNT(CASE WHEN STAGE = 'Negotiation' THEN 1 END) as neg_count,
                SUM(CASE WHEN STAGE = 'Negotiation' THEN AMOUNT ELSE 0 END) as neg_value,
                SUM(AMOUNT * PROBABILITY / 100) as weighted_value,
                SUM(PROBABILITY) / COUNT(*) as avg_probability
            FROM OPPORTUNITIES
            WHERE STATUS = 'Active'
            """
            
            result = self.da.execute_query(sql, fetch_one=True)
            
            return OpportunitySummary(
                total_opportunities=result['TOTAL_OPPORTUNITIES'],
                total_value=result['TOTAL_VALUE'] or 0,
                average_deal_size=result['AVG_AMOUNT'] or 0,
                by_stage={
                    'Qualification': {
                        'count': result['QUAL_COUNT'],
                        'value': result['QUAL_VALUE'] or 0
                    },
                    'Proposal': {
                        'count': result['PROP_COUNT'],
                        'value': result['PROP_VALUE'] or 0
                    },
                    'Negotiation': {
                        'count': result['NEG_COUNT'],
                        'value': result['NEG_VALUE'] or 0
                    }
                },
                win_probability_weighted=result['AVG_PROBABILITY'] or 0
            )
        
        except Exception as e:
            logger.error(f"Failed to get opportunity summary: {str(e)}")
            raise
    
    def create(self, opportunity: OpportunityCreate, created_by: str) -> Opportunity:
        """Create new opportunity"""
        try:
            sql = f"""
            INSERT INTO {self.TABLE}
            (NAME, ACCOUNT_ID, AMOUNT, CURRENCY, STAGE, PROBABILITY, 
             CLOSE_DATE, DESCRIPTION, STATUS, CREATED_DATE, CREATED_BY)
            VALUES (:0, :1, :2, :3, :4, :5, :6, :7, :8, SYSTIMESTAMP, :9)
            """
            
            params = {
                '0': opportunity.name,
                '1': opportunity.account_id,
                '2': opportunity.amount,
                '3': opportunity.currency,
                '4': opportunity.stage,
                '5': opportunity.probability,
                '6': opportunity.close_date,
                '7': opportunity.description,
                '8': opportunity.status,
                '9': created_by,
            }
            
            self.da.execute_update(sql, params, commit=True)
            logger.info(f"Created opportunity: {opportunity.name}")
            
            # Retrieve created record
            query = (OracleQueryBuilder()
                    .select(*self.COLUMNS)
                    .from_table(self.TABLE)
                    .where("NAME", "=", opportunity.name)
                    .order_by("CREATED_DATE", "DESC"))
            
            sql, qparams = query.build()
            result = self.da.execute_query(sql, qparams, fetch_one=True)
            
            return Opportunity(**result)
        
        except Exception as e:
            logger.error(f"Failed to create opportunity: {str(e)}")
            raise
    
    def update(self, id: int, update: OpportunityUpdate, modified_by: str) -> bool:
        """Update opportunity"""
        try:
            updates = []
            params = {}
            param_idx = 0
            
            if update.name:
                updates.append(f"NAME = :{param_idx}")
                params[str(param_idx)] = update.name
                param_idx += 1
            
            if update.stage:
                updates.append(f"STAGE = :{param_idx}")
                params[str(param_idx)] = update.stage
                param_idx += 1
            
            if update.amount:
                updates.append(f"AMOUNT = :{param_idx}")
                params[str(param_idx)] = update.amount
                param_idx += 1
            
            if update.probability is not None:
                updates.append(f"PROBABILITY = :{param_idx}")
                params[str(param_idx)] = update.probability
                param_idx += 1
            
            if update.close_date:
                updates.append(f"CLOSE_DATE = :{param_idx}")
                params[str(param_idx)] = update.close_date
                param_idx += 1
            
            if update.status:
                updates.append(f"STATUS = :{param_idx}")
                params[str(param_idx)] = update.status
                param_idx += 1
            
            if not updates:
                return False
            
            updates.append(f"MODIFIED_DATE = SYSTIMESTAMP")
            updates.append(f"MODIFIED_BY = :{param_idx}")
            params[str(param_idx)] = modified_by
            
            sql = f"UPDATE {self.TABLE} SET {', '.join(updates)} WHERE ID = :{param_idx + 1}"
            params[str(param_idx + 1)] = id
            
            rows_affected = self.da.execute_update(sql, params, commit=True)
            logger.info(f"Updated opportunity {id}")
            
            return rows_affected > 0
        
        except Exception as e:
            logger.error(f"Failed to update opportunity {id}: {str(e)}")
            raise
    
    def delete(self, id: int) -> bool:
        """Delete opportunity (soft delete)"""
        try:
            sql = f"UPDATE {self.TABLE} SET STATUS = 'Inactive', MODIFIED_DATE = SYSTIMESTAMP WHERE ID = :0"
            params = {'0': id}
            
            rows_affected = self.da.execute_update(sql, params, commit=True)
            logger.info(f"Deleted opportunity {id}")
            
            return rows_affected > 0
        
        except Exception as e:
            logger.error(f"Failed to delete opportunity {id}: {str(e)}")
            raise
    
    def batch_create(self, batch: BatchOpportunityCreate) -> BatchOperationResult:
        """Create multiple opportunities in a single operation"""
        try:
            successful = 0
            failed = 0
            errors = []
            
            operations = []
            for opp in batch.opportunities:
                sql = f"""
                INSERT INTO {self.TABLE}
                (NAME, ACCOUNT_ID, AMOUNT, CURRENCY, STAGE, PROBABILITY,
                 CLOSE_DATE, DESCRIPTION, STATUS, CREATED_DATE, CREATED_BY)
                VALUES (:0, :1, :2, :3, :4, :5, :6, :7, :8, SYSTIMESTAMP, :9)
                """
                
                params = {
                    '0': opp.name,
                    '1': opp.account_id,
                    '2': opp.amount,
                    '3': opp.currency,
                    '4': opp.stage,
                    '5': opp.probability,
                    '6': opp.close_date,
                    '7': opp.description,
                    '8': opp.status,
                    '9': batch.created_by,
                }
                
                operations.append((sql, params))
            
            # Execute as transaction
            try:
                self.da.execute_transaction(operations)
                successful = len(batch.opportunities)
            except OracleTransactionError as e:
                # If transaction fails, try individually
                for op in operations:
                    try:
                        self.da.execute_update(op[0], op[1], commit=True)
                        successful += 1
                    except Exception as item_err:
                        failed += 1
                        errors.append({'sql': op[0][:100], 'error': str(item_err)})
            
            logger.info(f"Batch operation: {successful} successful, {failed} failed")
            
            return BatchOperationResult(
                total=len(batch.opportunities),
                successful=successful,
                failed=failed,
                errors=errors
            )
        
        except Exception as e:
            logger.error(f"Batch create failed: {str(e)}")
            raise


if __name__ == "__main__":
    print("Repository Pattern - Senior-Level Data Access")
    print("=" * 60)
    print("""
    The repository pattern provides:
    
    1. Data Access Abstraction
       - Isolates business logic from data layer
       - Easy to test with mocks
       - Flexible underlying storage
    
    2. Common Operations
       - CRUD operations (Create, Read, Update, Delete)
       - Filtering and pagination
       - Aggregations and summaries
    
    3. Error Handling
       - Consistent error handling
       - Logging at each operation
       - Type-safe results
    
    4. Performance
       - Query optimization
       - Index utilization
       - Batch operations
    
    5. Maintainability
       - Single responsibility
       - Easy to extend
       - Clear interfaces
    
    See FastAPI endpoints for usage examples.
    """)
