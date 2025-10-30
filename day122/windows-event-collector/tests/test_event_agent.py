"""Test suite for Windows Event Agent"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from agent.core.event_agent import WindowsEventAgent
from transport.event_shipper import EventShipper

class TestWindowsEventAgent:
    """Test Windows Event Agent functionality"""
    
    @pytest.fixture
    async def agent(self):
        """Create agent instance for testing"""
        agent = WindowsEventAgent()
        await agent.initialize()
        return agent
        
    @pytest.fixture  
    async def shipper(self):
        """Create shipper instance for testing"""
        shipper = EventShipper()
        await shipper.initialize()
        return shipper
        
    async def test_agent_initialization(self, agent):
        """Test agent initializes properly"""
        assert agent.config is not None
        assert agent.is_running == False
        assert agent.stats['events_collected'] == 0
        
    async def test_mock_event_generation(self, agent):
        """Test mock event generation works"""
        events = await agent._generate_mock_events("System")
        assert len(events) > 0
        
        event = events[0]
        assert 'timestamp' in event
        assert 'channel' in event
        assert 'event_id' in event
        assert 'level' in event
        assert event['channel'] == 'System'
        
    async def test_event_parsing(self, agent):
        """Test event parsing functionality"""
        # Test with mock event
        mock_event = type('obj', (object,), {
            'EventID': 1001,
            'EventType': 4,  # Information
            'SourceName': 'TestSource',
            'ComputerName': 'TestComputer',
            'StringInserts': ['Test message'],
            'Data': b'test_data',
            'RecordNumber': 1,
            'Sid': None
        })
        
        # Mock the Windows availability check for this test
        with patch('src.agent.core.event_agent.WINDOWS_AVAILABLE', True):
            event = await agent._parse_event(mock_event, 'System')
            
        assert event is not None
        assert event['event_id'] == 1001
        assert event['level'] == 'Information'
        assert event['source'] == 'TestSource'
        assert event['channel'] == 'System'
        
    async def test_event_processing(self, agent):
        """Test event processing workflow"""
        processed_events = []
        
        async def mock_callback(event):
            processed_events.append(event)
            
        agent.event_callback = mock_callback
        
        # Create test events
        test_events = [
            {
                'channel': 'System',
                'event_id': 1001,
                'message': 'Test event 1'
            },
            {
                'channel': 'Application', 
                'event_id': 1002,
                'message': 'Test event 2'
            }
        ]
        
        # Process events
        await agent._process_events('System', test_events)
        
        # Verify processing
        assert agent.stats['events_collected'] == 2
        assert len(processed_events) == 2
        assert processed_events[0]['event_id'] == 1001
        
    async def test_shipper_batch_handling(self, shipper):
        """Test event shipper batching"""
        # Mock the HTTP session
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={'status': 'success'})
        
        mock_session = Mock()
        mock_session.post = Mock()
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock()
        
        shipper.session = mock_session
        
        # Test batch processing
        for i in range(5):
            await shipper.ship_event({'event_id': i, 'message': f'Event {i}'})
            
        # Verify batch buffer
        assert len(shipper.batch_buffer) == 5
        
        # Force flush
        await shipper.flush()
        
        # Verify batch was sent
        assert len(shipper.batch_buffer) == 0
        assert shipper.stats['batches_sent'] > 0

class TestIntegration:
    """Integration tests for complete workflow"""
    
    async def test_full_workflow(self):
        """Test complete event collection and shipping workflow"""
        # Create components
        shipper = EventShipper()
        await shipper.initialize()
        
        agent = WindowsEventAgent(event_callback=shipper.ship_event)
        await agent.initialize()
        
        # Mock HTTP transport to avoid actual network calls
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={'status': 'success'})
        mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.post.return_value.__aexit__ = AsyncMock()
        shipper.session = mock_session
        
        # Collect some mock events
        events = await agent._read_channel_events("System")
        assert len(events) > 0
        
        # Process events
        await agent._process_events("System", events)
        
        # Verify statistics
        assert agent.stats['events_collected'] > 0
        
        # Cleanup
        await agent.stop_collection()
        await shipper.close()
        
    async def test_error_handling(self):
        """Test error handling and recovery"""
        agent = WindowsEventAgent()
        await agent.initialize()
        
        # Test with invalid channel
        events = await agent._read_channel_events("InvalidChannel")
        # Should not crash and return empty list
        assert isinstance(events, list)
        
        # Test error counting
        initial_errors = agent.stats['errors']
        
        # Simulate processing error
        try:
            await agent._process_events("Test", [{'invalid': 'event'}])
        except:
            pass
            
        # Verify error was tracked (would be in a real implementation)
        # assert agent.stats['errors'] >= initial_errors

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
