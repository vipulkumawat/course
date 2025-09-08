#!/bin/bash

echo "🎬 Day 105: Automated Backup and Recovery Demo"
echo "=============================================="

# Ensure system is built
if [ ! -d "venv" ]; then
    echo "🔨 Building system first..."
    ./build.sh
fi

source venv/bin/activate
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

echo ""
echo "📦 Step 1: Creating demonstration backups..."
cd src

# Create full backup
python -c "
import asyncio
from backup.backup_engine import BackupEngine
from config.backup_config import BackupStrategy

async def create_demo_backups():
    engine = BackupEngine()
    
    print('📦 Creating full backup...')
    full_result = await engine.create_backup(BackupStrategy.FULL, 'demo_full_backup')
    if full_result['success']:
        print(f'   ✅ Full backup: {full_result[\"file_count\"]} files, {full_result[\"size_bytes\"]} bytes')
    
    print('📦 Creating incremental backup...')
    inc_result = await engine.create_backup(BackupStrategy.INCREMENTAL, 'demo_incremental_backup')
    if inc_result['success']:
        print(f'   ✅ Incremental backup: {inc_result[\"file_count\"]} files, {inc_result[\"size_bytes\"]} bytes')

asyncio.run(create_demo_backups())
"

echo ""
echo "✅ Step 2: Validating backups..."
python -c "
import asyncio
from validation.validator import BackupValidator
from pathlib import Path

async def validate_demo_backups():
    validator = BackupValidator()
    backup_dir = Path('../backups')
    
    backup_files = list(backup_dir.glob('demo_*full*.tar.gz'))
    if backup_files:
        backup_file = backup_files[0]
        metadata_file = backup_file.parent / f'{backup_file.stem.replace(\"_full\", \"\")}_metadata.json'
        
        if backup_file.exists() and metadata_file.exists():
            print(f'🔍 Validating: {backup_file.name}')
            result = await validator.validate_backup_integrity(str(backup_file), str(metadata_file))
            
            print(f'   Overall result: {result[\"overall_result\"]}')
            for test_name, test_result in result['tests'].items():
                status = '✅' if test_result['passed'] else '❌'
                print(f'   {status} {test_name}')

asyncio.run(validate_demo_backups())
"

echo ""
echo "🔄 Step 3: Testing recovery..."
python -c "
import asyncio
from recovery.recovery_manager import RecoveryManager

async def test_demo_recovery():
    manager = RecoveryManager()
    
    print('📋 Available backups:')
    backups = await manager.list_available_backups()
    
    for i, backup in enumerate(backups[:3]):
        print(f'   {i+1}. {backup[\"backup_id\"]} ({backup[\"strategy\"]}) - {backup[\"file_count\"]} files')
    
    if backups:
        print(f'🔄 Testing recovery from: {backups[0][\"backup_id\"]}')
        result = await manager.recover_from_backup(backups[0]['backup_id'], '../recovery/demo_restore')
        
        if result['success']:
            print(f'   ✅ Recovery successful: {result[\"extracted_files\"]} files extracted')
            print(f'   Duration: {result[\"duration_seconds\"]:.2f}s')
        else:
            print(f'   ❌ Recovery failed: {result.get(\"error\", \"Unknown error\")}')

asyncio.run(test_demo_recovery())
"

cd ..

echo ""
echo "📊 Step 4: Generating system statistics..."
echo "Backup directory contents:"
ls -la backups/ 2>/dev/null || echo "   No backups directory yet"

echo ""
echo "Recovery directory contents:"
ls -la recovery/ 2>/dev/null || echo "   No recovery directory yet"

echo ""
echo "🎉 Demo completed successfully!"
echo ""
echo "🌐 To see the web dashboard:"
echo "   1. Run: ./start.sh"
echo "   2. Open: http://localhost:8105"
echo "   3. Watch real-time backup monitoring"
echo ""
echo "🔧 Manual operations:"
echo "   - Create backup: cd src && python -c \"import asyncio; from backup.backup_engine import *; asyncio.run(BackupEngine().create_backup(BackupStrategy.FULL, 'manual_backup'))\""
echo "   - List backups: cd src && python recovery/recovery_manager.py list"
echo "   - Restore backup: cd src && python recovery/recovery_manager.py recover <backup_id>"
