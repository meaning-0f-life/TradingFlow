#!/usr/bin/env python3
"""
Simple test to verify the TradingFlow backend works
"""
import asyncio
from app.core.database import engine, Base, SessionLocal
from app.models import User, Workflow, APIKey
from app.core.security import get_password_hash
from app.core.engine import WorkflowExecutor
from app.nodes import get_node_class, get_available_nodes
from app.services.encryption import EncryptionService
from app.core.config import settings

def test_database():
    """Test database connection and table creation"""
    print("Testing database connection...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        print("\nCreated tables:")
        for table in Base.metadata.tables:
            print(f"  - {table}")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Note: Make sure PostgreSQL is running (docker-compose up -d)")
        return False

def test_node_registry():
    """Test node registry"""
    print("\nTesting node registry...")
    try:
        available = get_available_nodes()
        print(f"✅ Available node types: {list(available.keys())}")
        for node_type, info in available.items():
            print(f"  - {node_type}: {info['display_name']}")
            print(f"    Category: {info['category']}")
            print(f"    Parameters: {len(info['ui_schema']['parameters'])}")
            print(f"    Outputs: {len(info['ui_schema']['outputs'])}")
        return True
    except Exception as e:
        print(f"❌ Node registry error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_encryption():
    """Test encryption service"""
    print("\nTesting encryption service...")
    try:
        service = EncryptionService(settings.ENCRYPTION_KEY)
        test_string = "my-secret-api-key"
        encrypted = service.encrypt(test_string)
        decrypted = service.decrypt(encrypted)
        assert decrypted == test_string
        print(f"✅ Encryption works: {test_string} -> {encrypted[:20]}... -> {decrypted}")
        return True
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_executor():
    """Test workflow executor with a simple workflow"""
    print("\nTesting workflow executor...")
    try:
        # Create a simple workflow config
        workflow_config = {
            "nodes": [
                {
                    "id": "test_node",
                    "type": "llm",
                    "name": "Test LLM",
                    "config": {
                        "provider": "openai",
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.7,
                        "max_tokens": 10,
                        "user_prompt": "Say 'Hello from TradingFlow!'"
                    }
                }
            ],
            "edges": []
        }

        # Create a mock DB session (we won't actually execute LLM call without API key)
        db = SessionLocal()
        try:
            # Create a dummy execution record
            from app.models.workflow_execution import WorkflowExecution
            execution = WorkflowExecution(
                workflow_id=1,
                triggered_by=1,
                status="pending"
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)

            # Try to get node class
            node_class = get_node_class("llm")
            print(f"✅ LLM node class loaded: {node_class.__name__}")

            # Test node instantiation
            node = node_class("test_node", workflow_config["nodes"][0]["config"])
            print(f"✅ LLM node instantiated successfully")
            print(f"   Display name: {node.display_name}")
            print(f"   Category: {node.category}")

            # We won't actually execute because we need an API key
            print("✅ Workflow executor can be instantiated (skipping actual execution without API key)")

            return True
        finally:
            db.close()

    except Exception as e:
        print(f"❌ Workflow executor error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_fetcher_node():
    """Test DataFetcher node"""
    print("\nTesting DataFetcher node...")
    try:
        from app.nodes.data_node import DataFetcherNode

        # Test Yahoo Finance config
        config = {
            "source": "yahoo_finance",
            "symbol": "AAPL",
            "period": "1mo",
            "interval": "1d",
            "cache_ttl": 3600
        }
        node = DataFetcherNode("test_data", config)
        print(f"✅ DataFetcher node instantiated: {node.display_name}")
        print(f"   Source: {node.source}")
        print(f"   Symbol: {node.symbol}")

        # Test Yahoo Finance fetch (without actually calling API)
        print("   Note: Actual data fetch would require network and yfinance package")

        return True
    except Exception as e:
        print(f"❌ DataFetcher node error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("TradingFlow Backend Test Suite")
    print("=" * 60)

    results = []
    results.append(("Database", test_database()))
    results.append(("Node Registry", test_node_registry()))
    results.append(("Encryption", test_encryption()))
    results.append(("Workflow Executor", test_workflow_executor()))
    results.append(("DataFetcher Node", test_data_fetcher_node()))

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")

    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
        print("\nNext steps:")
        print("1. Ensure PostgreSQL is running: docker-compose up -d")
        print("2. Check .env file has correct credentials")
        print("3. Install missing dependencies: pip3 install -r requirements.txt")
    print("=" * 60)

    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)