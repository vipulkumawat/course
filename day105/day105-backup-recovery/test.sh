#!/bin/bash

set -e

echo "🧪 Running Day 105 Tests"
echo "========================"

# Ensure virtual environment is activated
source venv/bin/activate

# Ensure PYTHONPATH is set
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo "🔍 Running unit tests..."
python -m pytest tests/ -v --tb=short

echo ""
echo "🔧 Testing backup engine manually..."
cd src
python -c "
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
sys.path.append(str(Path.cwd().parent))

from backup.backup_engine import BackupEngine
from config.backup_config import BackupStrategy

async def test_backup():
    print('🔄 Creating backup engine...')
    engine = BackupEngine()
    
    print('📦 Creating full backup...')
    result = await engine.create_backup(BackupStrategy.FULL, 'test_manual_backup')
    
    if result['success']:
        print(f'✅ Backup successful: {result[\"backup_id\"]}')
        print(f'   Files: {result[\"file_count\"]}')
        print(f'   Size: {result[\"size_bytes\"]} bytes')
        print(f'   Duration: {result[\"duration_seconds\"]:.2f}s')
    else:
        print(f'❌ Backup failed: {result.get(\"error\", \"Unknown error\")}')

asyncio.run(test_backup())
"
cd ..

echo ""
echo "🔧 Testing recovery manager..."
cd src
python -c "
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
sys.path.append(str(Path.cwd().parent))

from recovery.recovery_manager import RecoveryManager

async def test_recovery():
    print('🔄 Creating recovery manager...')
    manager = RecoveryManager()
    
    print('📋 Listing available backups...')
    backups = await manager.list_available_backups()
    
    print(f'✅ Found {len(backups)} available backups')
    for backup in backups[:3]:
        print(f'   - {backup[\"backup_id\"]} ({backup[\"strategy\"]}) - {backup[\"file_count\"]} files')

asyncio.run(test_recovery())
"
cd ..

echo ""
echo "🔧 Testing validator..."
cd src
python -c "
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
sys.path.append(str(Path.cwd().parent))

from validation.validator import BackupValidator
from backup.backup_engine import BackupEngine
from config.backup_config import BackupStrategy

async def test_validation():
    print('🔄 Creating validator...')
    validator = BackupValidator()
    
    # Create a backup to validate
    engine = BackupEngine()
    backup_result = await engine.create_backup(BackupStrategy.FULL, 'test_validation')
    
    if backup_result['success']:
        print('✅ Test backup created, validating...')
        validation_result = await validator.validate_backup_integrity(
            backup_result['backup_path'],
            backup_result['metadata_path']
        )
        
        print(f'   Overall result: {validation_result[\"overall_result\"]}')
        for test_name, test_result in validation_result['tests'].items():
            status = '✅' if test_result['passed'] else '❌'
            print(f'   {status} {test_name}: {test_result.get(\"message\", \"OK\")}')

asyncio.run(test_validation())
"
cd ..

echo ""
echo "✅ All tests completed!"
echo ""
echo "🌐 To test the web dashboard:"
echo "   1. Run: ./start.sh"
echo "   2. Open: http://localhost:8105"
