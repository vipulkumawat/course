import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

// Mock fetch for tests
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      total_logs: 1000,
      error_rate: 2.5,
      avg_response_time: 125.5,
      active_services: 5
    }),
  })
);

beforeEach(() => {
  fetch.mockClear();
});

test('renders log visualization dashboard header', () => {
  render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
  const headerElement = screen.getByText(/Log Visualization Dashboard/i);
  expect(headerElement).toBeInTheDocument();
});

test('displays navigation links', () => {
  render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
  
  const dashboardLink = screen.getByText(/Dashboard/i);
  const chartsLink = screen.getByText(/Charts/i);
  
  expect(dashboardLink).toBeInTheDocument();
  expect(chartsLink).toBeInTheDocument();
});

test('shows connection status', () => {
  render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
  
  // Should show either Connected or Disconnected
  const statusElement = screen.getByText(/Connected|Disconnected/i);
  expect(statusElement).toBeInTheDocument();
});
