"""
Unit tests for Oracle integration components with mocks and fixtures.

Demonstrates senior-level testing patterns:
- Mocking external dependencies (Oracle database)
- Fixture-based test organization
- Parametrized tests for multiple scenarios
- Error handling and edge cases
- Transaction testing

Run with: pytest src/test_oracle_components.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import date, datetime, timedelta
from decimal import Decimal
import json

# Import modules under test
from .oracle_integration import (
    OracleConfig, OracleConnectionPool, OracleQueryBuilder,
    OracleDataAccess, OracleException, OracleQueryError
)
from .oracle_models import (
    Account, AccountCreate, AccountUpdate, Contact, ContactCreate,
    Opportunity, OpportunityCreate, OpportunityUpdate, OpportunityStage,
    AccountType, RecordStatus, OpportunityFilter, OpportunitySummary,
    BatchOpportunityCreate
)
from .oracle_repository import (
    AccountRepository, OpportunityRepository
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def oracle_config():
    """Create test Oracle configuration."""
    return OracleConfig(
        host="localhost",
        port=1521,
        service_name="XE",
        user="test_user",
        password="test_password",
        pool_min=1,
        pool_max=5,
        pool_increment=1,
        encoding="UTF-8"
    )


@pytest.fixture
def mock_pool():
    """Create mock connection pool."""
    pool = Mock(spec=OracleConnectionPool)
    pool.execute_query = Mock()
    pool.execute_update = Mock()
    pool.call_procedure = Mock()
    pool.get_metrics = Mock(return_value={
        'queries_executed': 10,
        'query_errors': 0,
        'total_query_time': 100.5
    })
    pool.health_check = Mock(return_value={
        'status': 'healthy',
        'active_connections': 3,
        'idle_connections': 2
    })
    return pool


@pytest.fixture
def data_access(mock_pool):
    """Create OracleDataAccess with mocked pool."""
    return OracleDataAccess(mock_pool)


@pytest.fixture
def account_data():
    """Sample account data for testing."""
    return {
        'id': 1,
        'name': 'Acme Corporation',
        'industry': 'Technology',
        'account_type': 'Customer',
        'phone': '555-0100',
        'website': 'https://acme.com',
        'employee_count': 1500,
        'annual_revenue': 500_000_000,
        'status': 'Active',
        'created_date': datetime.now(),
        'modified_date': datetime.now(),
        'created_by': 'john.doe@company.com',
        'modified_by': 'jane.smith@company.com'
    }


@pytest.fixture
def opportunity_data():
    """Sample opportunity data for testing."""
    return {
        'id': 1,
        'name': 'Enterprise License Deal',
        'account_id': 1,
        'contact_id': None,
        'amount': 250_000,
        'currency': 'USD',
        'stage': 'Proposal',
        'probability': 75,
        'close_date': date(2026, 3, 31),
        'description': 'Year 1 license agreement',
        'status': 'Active',
        'fiscal_quarter': '2026-Q1',
        'forecast_category': 'Pipeline',
        'created_date': datetime.now(),
        'modified_date': datetime.now(),
        'created_by': 'sales@company.com',
        'modified_by': 'sales@company.com'
    }


# ============================================================================
# OracleConfig Tests
# ============================================================================

class TestOracleConfig:
    """Test Oracle configuration."""

    def test_config_creation(self, oracle_config):
        """Test configuration object creation."""
        assert oracle_config.host == "localhost"
        assert oracle_config.port == 1521
        assert oracle_config.service_name == "XE"
        assert oracle_config.user == "test_user"
        assert oracle_config.password == "test_password"
        assert oracle_config.pool_min == 1
        assert oracle_config.pool_max == 5

    @patch.dict('os.environ', {
        'ORACLE_HOST': 'db.example.com',
        'ORACLE_PORT': '1521',
        'ORACLE_SERVICE_NAME': 'ORCL',
        'ORACLE_USER': 'app_user',
        'ORACLE_PASSWORD': 'secret'
    })
    def test_config_from_env(self):
        """Test loading configuration from environment variables."""
        config = OracleConfig.from_env()
        assert config.host == 'db.example.com'
        assert config.user == 'app_user'
        assert config.password == 'secret'

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = OracleConfig(
            host="localhost",
            port=1521,
            service_name="XE",
            user="user",
            password="pass"
        )
        assert config.port == 1521

        # Pool constraints
        config.pool_max = 100
        config.pool_min = 80
        assert config.pool_max >= config.pool_min


# ============================================================================
# OracleQueryBuilder Tests
# ============================================================================

class TestOracleQueryBuilder:
    """Test SQL query builder."""

    def test_simple_select(self):
        """Test building simple SELECT query."""
        query = (OracleQueryBuilder()
                 .select('ID', 'NAME')
                 .from_table('ACCOUNTS'))
        
        sql, params = query.build()
        assert sql == 'SELECT ID, NAME FROM ACCOUNTS'
        assert params == {}

    def test_select_with_where(self):
        """Test SELECT with WHERE clause."""
        query = (OracleQueryBuilder()
                 .select('ID', 'NAME', 'AMOUNT')
                 .from_table('ACCOUNTS')
                 .where('INDUSTRY', '=', 'Technology')
                 .where('ANNUAL_REVENUE', '>', 1_000_000))
        
        sql, params = query.build()
        assert 'WHERE' in sql
        assert 'INDUSTRY' in sql
        assert 'ANNUAL_REVENUE' in sql
        assert params['0'] == 'Technology'
        assert params['1'] == 1_000_000

    def test_where_in_clause(self):
        """Test WHERE IN clause for multiple values."""
        query = (OracleQueryBuilder()
                 .select('ID', 'NAME')
                 .from_table('OPPORTUNITIES')
                 .where_in('STAGE', ['Proposal', 'Negotiation', 'Closed Won']))
        
        sql, params = query.build()
        assert 'STAGE IN' in sql
        assert len(params) == 3

    def test_order_and_limit(self):
        """Test ORDER BY and LIMIT clauses."""
        query = (OracleQueryBuilder()
                 .select('ID', 'NAME', 'AMOUNT')
                 .from_table('OPPORTUNITIES')
                 .order_by('AMOUNT', 'DESC')
                 .limit(10)
                 .offset(0))
        
        sql, params = query.build()
        assert 'ORDER BY AMOUNT DESC' in sql
        assert 'LIMIT 10' in sql or 'FETCH FIRST 10 ROWS' in sql  # Oracle variant

    def test_join_query(self):
        """Test JOIN query construction."""
        query = (OracleQueryBuilder()
                 .select('A.ID', 'A.NAME', 'O.AMOUNT')
                 .from_table('ACCOUNTS A')
                 .join('OPPORTUNITIES O', 'A.ID = O.ACCOUNT_ID'))
        
        sql, params = query.build()
        assert 'JOIN' in sql or 'INNER JOIN' in sql
        assert 'ACCOUNTS A' in sql
        assert 'OPPORTUNITIES O' in sql

    def test_parameterized_query(self):
        """Test that parameters are properly parameterized (SQL injection prevention)."""
        malicious_input = "Tech'; DROP TABLE ACCOUNTS; --"
        
        query = (OracleQueryBuilder()
                 .select('ID', 'NAME')
                 .from_table('ACCOUNTS')
                 .where('INDUSTRY', '=', malicious_input))
        
        sql, params = query.build()
        
        # SQL should NOT contain malicious input directly
        assert malicious_input not in sql
        # Input should be in params
        assert malicious_input in params.values()

    def test_multiple_conditions(self):
        """Test multiple WHERE conditions."""
        query = (OracleQueryBuilder()
                 .select('*')
                 .from_table('OPPORTUNITIES')
                 .where('AMOUNT', '>', 100_000)
                 .where('PROBABILITY', '>=', 50)
                 .where('STAGE', '=', 'Proposal')
                 .where('STATUS', '=', 'Active'))
        
        sql, params = query.build()
        where_count = sql.count('WHERE')
        and_count = sql.count('AND')
        
        assert where_count >= 1
        assert and_count >= 3  # 4 conditions need 3 ANDs


# ============================================================================
# OracleDataAccess Tests
# ============================================================================

class TestOracleDataAccess:
    """Test data access layer."""

    def test_execute_query_returns_results(self, data_access, mock_pool):
        """Test executing SELECT query."""
        mock_pool.execute_query.return_value = [
            {'ID': 1, 'NAME': 'Acme'},
            {'ID': 2, 'NAME': 'Beta'}
        ]
        
        results = data_access.execute_query(
            'SELECT ID, NAME FROM ACCOUNTS',
            {}
        )
        
        assert len(results) == 2
        assert results[0]['NAME'] == 'Acme'
        mock_pool.execute_query.assert_called_once()

    def test_execute_query_single_row(self, data_access, mock_pool):
        """Test fetching single row with fetch_one."""
        mock_pool.execute_query.return_value = {'ID': 1, 'NAME': 'Acme'}
        
        result = data_access.execute_query(
            'SELECT ID, NAME FROM ACCOUNTS WHERE ID = :0',
            {'0': 1},
            fetch_one=True
        )
        
        assert result['ID'] == 1
        assert result['NAME'] == 'Acme'

    def test_execute_update_success(self, data_access, mock_pool):
        """Test INSERT/UPDATE/DELETE operation."""
        mock_pool.execute_update.return_value = 1
        
        rows_affected = data_access.execute_update(
            'UPDATE ACCOUNTS SET INDUSTRY = :0 WHERE ID = :1',
            {'0': 'Finance', '1': 1}
        )
        
        assert rows_affected == 1
        mock_pool.execute_update.assert_called_once()

    def test_call_procedure(self, data_access, mock_pool):
        """Test calling stored procedure."""
        mock_pool.call_procedure.return_value = {'OUTPUT': 42}
        
        result = data_access.call_procedure(
            'PKG_ACCOUNTS.calculate_value',
            ['input1', 'input2']
        )
        
        assert result['OUTPUT'] == 42
        mock_pool.call_procedure.assert_called_once()

    def test_execute_transaction_success(self, data_access, mock_pool):
        """Test multi-statement transaction."""
        mock_pool.execute_query.side_effect = [1, 2, 3]
        
        operations = [
            ('INSERT INTO ACCOUNTS ...', {'0': 'Acme'}),
            ('INSERT INTO CONTACTS ...', {'0': 1}),
            ('INSERT INTO OPPORTUNITIES ...', {'0': 100_000})
        ]
        
        results = data_access.execute_transaction(operations)
        
        assert len(results) == 3
        assert mock_pool.execute_query.call_count == 3

    def test_execute_transaction_failure_rollback(self, data_access, mock_pool):
        """Test transaction rollback on error."""
        mock_pool.execute_query.side_effect = [
            1,  # First operation succeeds
            OracleException("Foreign key violation")  # Second fails
        ]
        
        operations = [
            ('INSERT INTO ACCOUNTS ...', {'0': 'Acme'}),
            ('INSERT INTO CONTACTS ...', {'0': 999})  # Non-existent account
        ]
        
        with pytest.raises(OracleException):
            data_access.execute_transaction(operations)

    def test_query_error_handling(self, data_access, mock_pool):
        """Test error handling during query."""
        mock_pool.execute_query.side_effect = OracleQueryError("Syntax error")
        
        with pytest.raises(OracleQueryError):
            data_access.execute_query('INVALID SQL', {})

    def test_metrics_collection(self, data_access, mock_pool):
        """Test that metrics are collected."""
        mock_pool.get_metrics.return_value = {
            'queries_executed': 5,
            'query_errors': 1,
            'total_query_time': 250.5
        }
        
        metrics = data_access.get_metrics()
        
        assert metrics['queries_executed'] == 5
        assert metrics['query_errors'] == 1


# ============================================================================
# Oracle Models Tests
# ============================================================================

class TestOracleModels:
    """Test data models and validation."""

    def test_account_creation(self, account_data):
        """Test Account model creation."""
        account = Account(**account_data)
        
        assert account.id == 1
        assert account.name == 'Acme Corporation'
        assert account.industry == 'Technology'
        assert account.annual_revenue == 500_000_000

    def test_account_create_model(self):
        """Test AccountCreate model for POST requests."""
        create_data = {
            'name': 'New Corp',
            'industry': 'Finance',
            'account_type': 'Prospect',
            'employee_count': 500,
            'annual_revenue': 100_000_000
        }
        
        account = AccountCreate(**create_data)
        assert account.name == 'New Corp'
        assert account.annual_revenue == 100_000_000

    def test_account_validation_revenue_max(self):
        """Test revenue validation (max $1 trillion)."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            AccountCreate(
                name="TooRich",
                industry="Finance",
                account_type="Customer",
                annual_revenue=2_000_000_000_000  # 2 trillion - too much!
            )

    def test_opportunity_validation_stage_probability(self):
        """Test probability validation matches stage."""
        from pydantic import ValidationError
        
        # Proposal stage expects 25-75%
        valid = OpportunityCreate(
            name="Deal",
            account_id=1,
            amount=100_000,
            stage=OpportunityStage.PROPOSAL,
            probability=50,  # Valid for Proposal
            close_date=date(2026, 6, 30)
        )
        assert valid.probability == 50
        
        # Closed Won should be 100%
        won = OpportunityCreate(
            name="Won Deal",
            account_id=1,
            amount=100_000,
            stage=OpportunityStage.CLOSED_WON,
            probability=100,  # Must be 100%
            close_date=date(2026, 1, 1)
        )
        assert won.probability == 100

    def test_opportunity_validation_close_date_future(self):
        """Test close_date must be in future."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            OpportunityCreate(
                name="Past Deal",
                account_id=1,
                amount=100_000,
                stage=OpportunityStage.PROPOSAL,
                probability=75,
                close_date=date(2020, 1, 1)  # In the past!
            )

    def test_contact_validation_email(self):
        """Test email validation."""
        from pydantic import ValidationError
        
        # Valid email
        contact = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            account_id=1
        )
        assert contact.email == "john@example.com"
        
        # Invalid email
        with pytest.raises(ValidationError):
            ContactCreate(
                first_name="John",
                last_name="Doe",
                email="not-an-email",
                account_id=1
            )

    def test_batch_opportunity_create(self):
        """Test batch create model."""
        batch = BatchOpportunityCreate(
            opportunities=[
                OpportunityCreate(
                    name=f"Deal {i}",
                    account_id=1,
                    amount=100_000 * (i + 1),
                    stage=OpportunityStage.PROPOSAL,
                    probability=75,
                    close_date=date(2026, 6, 30)
                )
                for i in range(5)
            ],
            created_by="bulk_import@company.com"
        )
        
        assert len(batch.opportunities) == 5
        assert batch.opportunities[0].amount == 100_000
        assert batch.opportunities[4].amount == 500_000

    def test_opportunity_filter_model(self):
        """Test filtering model."""
        filter_query = OpportunityFilter(
            stage=OpportunityStage.PROPOSAL,
            min_amount=50_000,
            max_amount=500_000,
            min_probability=50,
            limit=100
        )
        
        assert filter_query.stage == OpportunityStage.PROPOSAL
        assert filter_query.min_amount == 50_000
        assert filter_query.limit == 100


# ============================================================================
# Repository Tests
# ============================================================================

class TestAccountRepository:
    """Test Account repository layer."""

    @pytest.fixture
    def account_repo(self, data_access):
        """Create AccountRepository with mocked data access."""
        return AccountRepository(data_access)

    def test_get_by_id(self, account_repo, data_access, account_data):
        """Test retrieving account by ID."""
        data_access.execute_query = Mock(return_value=account_data)
        
        account = account_repo.get_by_id(1)
        
        assert account.id == 1
        assert account.name == 'Acme Corporation'
        data_access.execute_query.assert_called_once()

    def test_get_all_with_pagination(self, account_repo, data_access):
        """Test getting all accounts with pagination."""
        data_access.execute_query = Mock(return_value=[
            {'id': 1, 'name': 'Acme', 'industry': 'Tech', ...},
            {'id': 2, 'name': 'Beta', 'industry': 'Finance', ...}
        ])
        
        accounts = account_repo.get_all(limit=50, offset=0)
        
        assert len(accounts) == 2
        # Verify LIMIT and OFFSET in query
        call_args = data_access.execute_query.call_args
        sql = call_args[0][0]
        assert 'LIMIT' in sql or 'FETCH' in sql

    def test_get_by_status(self, account_repo, data_access):
        """Test filtering by status."""
        data_access.execute_query = Mock(return_value=[
            {'id': 1, 'name': 'Active Account', 'status': 'Active', ...}
        ])
        
        accounts = account_repo.get_by_status(RecordStatus.ACTIVE)
        
        assert all(acc.status == RecordStatus.ACTIVE for acc in accounts)

    def test_create_account(self, account_repo, data_access):
        """Test creating new account."""
        create_data = AccountCreate(
            name="New Corp",
            industry="Technology",
            account_type="Prospect",
            employee_count=100,
            annual_revenue=50_000_000
        )
        
        data_access.execute_update = Mock(return_value=1)
        data_access.execute_query = Mock(return_value={
            'ID': 100,
            'NAME': 'New Corp',
            'INDUSTRY': 'Technology',
            ...
        })
        
        account = account_repo.create(create_data, created_by="admin")
        
        assert account.id == 100
        assert account.name == "New Corp"
        data_access.execute_update.assert_called_once()

    def test_update_account(self, account_repo, data_access):
        """Test updating account (partial update)."""
        update_data = AccountUpdate(industry="Finance", annual_revenue=150_000_000)
        
        data_access.execute_update = Mock(return_value=1)
        
        success = account_repo.update(1, update_data, modified_by="admin")
        
        assert success is True
        # Verify only provided fields are in UPDATE
        call_args = data_access.execute_update.call_args
        sql = call_args[0][0]
        assert 'INDUSTRY' in sql
        assert 'ANNUAL_REVENUE' in sql

    def test_soft_delete_account(self, account_repo, data_access):
        """Test soft delete (sets status to inactive)."""
        data_access.execute_update = Mock(return_value=1)
        
        success = account_repo.delete(1)
        
        assert success is True
        # Verify UPDATE not DELETE
        call_args = data_access.execute_update.call_args
        sql = call_args[0][0]
        assert 'UPDATE' in sql
        assert 'DELETE' not in sql


class TestOpportunityRepository:
    """Test Opportunity repository layer."""

    @pytest.fixture
    def opp_repo(self, data_access):
        """Create OpportunityRepository with mocked components."""
        account_repo = Mock(spec=AccountRepository)
        return OpportunityRepository(data_access, account_repo)

    def test_get_by_id(self, opp_repo, data_access, opportunity_data):
        """Test retrieving opportunity by ID."""
        data_access.execute_query = Mock(return_value=opportunity_data)
        
        opp = opp_repo.get_by_id(1)
        
        assert opp.id == 1
        assert opp.name == 'Enterprise License Deal'
        assert opp.amount == 250_000

    def test_get_by_account(self, opp_repo, data_access):
        """Test getting opportunities for specific account."""
        data_access.execute_query = Mock(return_value=[
            {'id': 1, 'account_id': 1, 'name': 'Deal 1', 'amount': 100_000, ...},
            {'id': 2, 'account_id': 1, 'name': 'Deal 2', 'amount': 150_000, ...}
        ])
        
        opps = opp_repo.get_by_account(1)
        
        assert len(opps) == 2
        assert all(opp.account_id == 1 for opp in opps)

    def test_get_by_stage(self, opp_repo, data_access):
        """Test filtering by stage."""
        data_access.execute_query = Mock(return_value=[
            {'id': 1, 'stage': 'Proposal', 'amount': 100_000, ...},
            {'id': 2, 'stage': 'Proposal', 'amount': 200_000, ...}
        ])
        
        opps = opp_repo.get_by_stage(OpportunityStage.PROPOSAL)
        
        assert all(opp.stage == OpportunityStage.PROPOSAL for opp in opps)

    def test_filter_complex(self, opp_repo, data_access):
        """Test complex filtering with multiple criteria."""
        filter_query = OpportunityFilter(
            stage=OpportunityStage.PROPOSAL,
            min_amount=100_000,
            max_amount=500_000,
            min_probability=50,
            limit=10
        )
        
        data_access.execute_query = Mock(return_value=[
            {'id': 1, 'stage': 'Proposal', 'amount': 250_000, 'probability': 75, ...}
        ])
        
        opps = opp_repo.filter(filter_query)
        
        assert len(opps) == 1
        # Verify WHERE clause has all conditions
        call_args = data_access.execute_query.call_args
        sql = call_args[0][0]
        assert 'STAGE' in sql
        assert 'AMOUNT' in sql
        assert 'PROBABILITY' in sql

    def test_get_summary(self, opp_repo, data_access):
        """Test pipeline summary aggregation."""
        data_access.execute_query = Mock(return_value=[
            {
                'TOTAL_OPPORTUNITIES': 45,
                'TOTAL_VALUE': 15_750_000,
                'STAGE_COUNTS': json.dumps({
                    'Qualification': 15,
                    'Proposal': 20,
                    'Negotiation': 10
                }),
                'AVERAGE_DEAL_SIZE': 350_000
            }
        ])
        
        summary = opp_repo.get_summary()
        
        assert summary.total_opportunities == 45
        assert summary.total_value == 15_750_000

    def test_batch_create_success(self, opp_repo, data_access):
        """Test batch creating opportunities."""
        batch = BatchOpportunityCreate(
            opportunities=[
                OpportunityCreate(
                    name=f"Deal {i}",
                    account_id=1,
                    amount=100_000,
                    stage=OpportunityStage.PROPOSAL,
                    probability=75,
                    close_date=date(2026, 6, 30)
                )
                for i in range(3)
            ],
            created_by="bulk@company.com"
        )
        
        data_access.execute_update = Mock(return_value=1)
        data_access.execute_query = Mock(side_effect=[
            {'ID': 1, 'name': 'Deal 0', ...},
            {'ID': 2, 'name': 'Deal 1', ...},
            {'ID': 3, 'name': 'Deal 2', ...}
        ])
        
        result = opp_repo.batch_create(batch)
        
        assert result.successful == 3
        assert result.failed == 0

    def test_batch_create_partial_failure(self, opp_repo, data_access):
        """Test batch with some records failing."""
        batch = BatchOpportunityCreate(
            opportunities=[
                OpportunityCreate(
                    name="Deal 1",
                    account_id=1,
                    amount=100_000,
                    stage=OpportunityStage.PROPOSAL,
                    probability=75,
                    close_date=date(2026, 6, 30)
                ),
                OpportunityCreate(
                    name="Deal 2",
                    account_id=999,  # Non-existent account
                    amount=100_000,
                    stage=OpportunityStage.PROPOSAL,
                    probability=75,
                    close_date=date(2026, 6, 30)
                )
            ],
            created_by="bulk@company.com"
        )
        
        data_access.execute_update = Mock(side_effect=[
            1,  # First succeeds
            OracleException("Foreign key constraint violated")  # Second fails
        ])
        
        result = opp_repo.batch_create(batch)
        
        assert result.successful >= 1
        assert result.failed >= 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestCompleteWorkflow:
    """End-to-end workflow tests."""

    def test_create_and_retrieve_account(self, data_access):
        """Test creating account and retrieving it."""
        create_sql = "INSERT INTO ACCOUNTS ..."
        select_sql = "SELECT * FROM ACCOUNTS WHERE ID = :0"
        
        data_access.execute_update = Mock(return_value=1)
        data_access.execute_query = Mock(return_value={
            'ID': 1,
            'NAME': 'Test Corp',
            'INDUSTRY': 'Tech',
            'STATUS': 'Active',
            ...
        })
        
        repo = AccountRepository(data_access)
        
        # Create
        account = repo.create(
            AccountCreate(
                name="Test Corp",
                industry="Tech",
                account_type="Customer"
            ),
            created_by="admin"
        )
        
        # Retrieve
        retrieved = repo.get_by_id(account.id)
        
        assert retrieved.name == "Test Corp"
        assert retrieved.industry == "Tech"

    def test_create_account_then_opportunity(self, data_access):
        """Test creating account and linked opportunity."""
        account_repo = AccountRepository(data_access)
        opp_repo = OpportunityRepository(data_access, account_repo)
        
        # Create account
        data_access.execute_update = Mock(return_value=1)
        data_access.execute_query = Mock(return_value={
            'ID': 1, 'NAME': 'Acme', 'INDUSTRY': 'Tech', ...
        })
        
        account = account_repo.create(
            AccountCreate(name="Acme", industry="Tech"),
            created_by="admin"
        )
        
        # Create opportunity for account
        data_access.execute_query = Mock(return_value={
            'ID': 1,
            'ACCOUNT_ID': account.id,
            'NAME': 'License Deal',
            'AMOUNT': 250_000,
            'STAGE': 'Proposal',
            ...
        })
        
        opp = opp_repo.create(
            OpportunityCreate(
                name="License Deal",
                account_id=account.id,
                amount=250_000,
                stage=OpportunityStage.PROPOSAL,
                probability=75,
                close_date=date(2026, 6, 30)
            ),
            created_by="sales"
        )
        
        assert opp.account_id == account.id
        assert opp.amount == 250_000


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_connection_timeout(self, data_access, mock_pool):
        """Test handling connection timeout."""
        mock_pool.execute_query.side_effect = OracleException(
            "Connection timeout"
        )
        
        with pytest.raises(OracleException):
            data_access.execute_query("SELECT * FROM ACCOUNTS", {})

    def test_invalid_sql_syntax(self, data_access, mock_pool):
        """Test handling SQL syntax errors."""
        mock_pool.execute_query.side_effect = OracleQueryError(
            "ORA-00923: FROM keyword not found where expected"
        )
        
        with pytest.raises(OracleQueryError):
            data_access.execute_query("INVALID SQL", {})

    def test_foreign_key_violation(self, data_access, mock_pool):
        """Test handling foreign key constraint."""
        mock_pool.execute_update.side_effect = OracleException(
            "ORA-02291: integrity constraint violated"
        )
        
        repo = AccountRepository(data_access)
        
        with pytest.raises(OracleException):
            repo.create(
                AccountCreate(
                    name="Test",
                    industry="Tech",
                    account_type="Customer"
                ),
                created_by="admin"
            )

    def test_duplicate_key_error(self, data_access, mock_pool):
        """Test handling unique constraint violation."""
        mock_pool.execute_update.side_effect = OracleException(
            "ORA-00001: unique constraint violated"
        )
        
        repo = AccountRepository(data_access)
        
        with pytest.raises(OracleException):
            repo.create(
                AccountCreate(
                    name="Duplicate",
                    industry="Tech",
                    account_type="Customer"
                ),
                created_by="admin"
            )


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""

    def test_large_batch_create(self, data_access):
        """Test batch creating 100 opportunities."""
        opps = [
            OpportunityCreate(
                name=f"Bulk Deal {i}",
                account_id=1,
                amount=100_000 * (i + 1),
                stage=OpportunityStage.PROPOSAL,
                probability=75,
                close_date=date(2026, 6, 30)
            )
            for i in range(100)
        ]
        
        batch = BatchOpportunityCreate(
            opportunities=opps,
            created_by="bulk@company.com"
        )
        
        repo = OpportunityRepository(data_access, Mock())
        data_access.execute_update = Mock(return_value=1)
        data_access.execute_query = Mock(side_effect=[
            {'ID': i+1, 'NAME': f'Bulk Deal {i}', ...}
            for i in range(100)
        ])
        
        result = repo.batch_create(batch)
        
        assert result.successful == 100
        assert result.failed == 0

    def test_complex_aggregation_query(self, data_access):
        """Test complex aggregation performance."""
        repo = OpportunityRepository(data_access, Mock())
        
        data_access.execute_query = Mock(return_value=[
            {
                'TOTAL_OPPORTUNITIES': 1000,
                'TOTAL_VALUE': 50_000_000,
                'AVERAGE_DEAL_SIZE': 50_000
            }
        ])
        
        summary = repo.get_summary()
        
        assert summary.total_opportunities == 1000


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
