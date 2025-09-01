import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import PreferencesPage from './PreferencesPage';

const queryClient = new QueryClient();

const renderWithProviders = (component) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

test('renders preferences page', () => {
  renderWithProviders(<PreferencesPage />);
  expect(screen.getByText('User Preferences')).toBeInTheDocument();
});

test('displays preference categories', () => {
  renderWithProviders(<PreferencesPage />);
  expect(screen.getByText('Dashboard')).toBeInTheDocument();
  expect(screen.getByText('Notifications')).toBeInTheDocument();
  expect(screen.getByText('Theme')).toBeInTheDocument();
});
