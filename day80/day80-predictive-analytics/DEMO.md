# 🎬 Predictive Analytics Demo

## Demo Button Functionality

The dashboard now includes a **"Run Demo"** button that demonstrates the full predictive analytics pipeline in action.

### What the Demo Does

When you click the **🎬 Run Demo** button, it will:

1. **📊 Generate Sample Log Data**
   - Creates realistic web server response time logs
   - Generates database performance logs
   - Creates error logs with patterns
   - Saves data to CSV files in the `data/` directory

2. **🤖 Train Forecasting Models**
   - Trains ARIMA model for time series forecasting
   - Trains Prophet model for trend analysis
   - Trains Exponential Smoothing model
   - Saves trained models to `models/trained/` directory

3. **🔮 Generate Ensemble Predictions**
   - Combines predictions from all models
   - Calculates confidence intervals
   - Generates 12-step forecast (60 minutes ahead)
   - Updates the dashboard with real predictions

4. **🔄 Update Dashboard**
   - Refreshes all charts and metrics
   - Shows individual model predictions
   - Displays confidence levels
   - Updates system health status

### How to Use

1. **Access the Dashboard**: Open http://localhost:3000 in your browser
2. **Click Demo Button**: Look for the **🎬 Run Demo** button in the header
3. **Watch Progress**: The button will show progress messages as it runs
4. **View Results**: Once complete, you'll see real forecasting data on the dashboard

### Demo Features

- **Real-time Progress**: Shows step-by-step progress during execution
- **Visual Feedback**: Button animates and changes color while running
- **Error Handling**: Displays helpful error messages if something goes wrong
- **Auto-refresh**: Dashboard automatically updates with new data

### Expected Results

After running the demo, you should see:

- **Ensemble Forecast Chart**: Shows predicted response times over the next hour
- **Individual Model Predictions**: Displays how each model predicts differently
- **Confidence Levels**: Shows prediction confidence (high/medium/low)
- **System Metrics**: Updated model performance and health status
- **Alert Levels**: Based on prediction confidence

### Technical Details

- **Data Generation**: Creates 7 days of realistic log data
- **Model Training**: Uses 80% of data for training, 20% for validation
- **Forecasting**: Generates 12 predictions (5-minute intervals)
- **Caching**: Results are cached in Redis for 5 minutes
- **Real-time**: Dashboard updates every 30 seconds

### Troubleshooting

If the demo fails:

1. **Check API Status**: Ensure the backend is running on port 8080
2. **Check Redis**: Make sure Redis server is running
3. **Check Logs**: Look for error messages in the progress indicator
4. **Restart Services**: Use `./stop.sh` and `./start.sh` if needed

The demo provides a complete end-to-end demonstration of the predictive analytics system's capabilities! 