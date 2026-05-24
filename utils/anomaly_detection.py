import pandas as pd
import numpy as np
from scipy import stats
import plotly.graph_objects as go
import streamlit as st

class AnomalyDetector:
    def __init__(self):
        self.anomalies = []
    
    def detect_anomalies(self, df, method='iqr'):
        """Detect sales anomalies using multiple methods"""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        anomalies = []
        
        if method == 'iqr':
            Q1 = df['sales'].quantile(0.25)
            Q3 = df['sales'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            anomalies = df[(df['sales'] < lower_bound) | (df['sales'] > upper_bound)]
        
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(df['sales']))
            anomalies = df[z_scores > 2.5]
        
        elif method == 'rolling':
            # Rolling window anomaly detection
            window = min(30, len(df) // 4)
            df['rolling_mean'] = df['sales'].rolling(window=window).mean()
            df['rolling_std'] = df['sales'].rolling(window=window).std()
            df['z_score'] = (df['sales'] - df['rolling_mean']) / df['rolling_std']
            anomalies = df[np.abs(df['z_score']) > 2.0].dropna()
        
        # Add anomaly type classification
        if not anomalies.empty:
            median_sales = df['sales'].median()
            anomalies['anomaly_type'] = anomalies['sales'].apply(
                lambda x: 'High Sales Spike' if x > median_sales else 'Low Sales Drop'
            )
            anomalies['severity'] = anomalies['sales'].apply(
                lambda x: 'Critical' if abs(x - median_sales) > 2 * df['sales'].std() else 'Moderate'
            )
        
        self.anomalies = anomalies
        return anomalies
    
    def plot_anomalies(self, df, anomalies):
        """Create interactive plot highlighting anomalies"""
        fig = go.Figure()
        
        # Normal sales data
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['sales'],
            mode='lines+markers',
            name='Sales',
            line=dict(color='blue', width=2),
            marker=dict(size=4)
        ))
        
        # Highlight anomalies
        if not anomalies.empty:
            fig.add_trace(go.Scatter(
                x=anomalies['date'],
                y=anomalies['sales'],
                mode='markers',
                name='Anomalies',
                marker=dict(
                    size=10,
                    color='red',
                    symbol='diamond',
                    line=dict(width=2, color='darkred')
                ),
                text=anomalies.get('anomaly_type', 'Anomaly'),
                hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Sales: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title='Sales Data with Anomaly Detection',
            xaxis_title='Date',
            yaxis_title='Sales',
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def get_anomaly_insights(self, anomalies):
        """Generate actionable insights from anomalies"""
        if anomalies.empty:
            return "No significant anomalies detected in your sales data."
        
        insights = []
        
        # Count by type
        if 'anomaly_type' in anomalies.columns:
            high_spikes = len(anomalies[anomalies['anomaly_type'] == 'High Sales Spike'])
            low_drops = len(anomalies[anomalies['anomaly_type'] == 'Low Sales Drop'])
            
            if high_spikes > 0:
                insights.append(f"🚀 Found {high_spikes} high sales spikes - investigate what drove these peaks!")
            
            if low_drops > 0:
                insights.append(f"⚠️ Found {low_drops} sales drops - check for stock issues or external factors")
        
        # Recent anomalies
        recent_anomalies = anomalies[anomalies['date'] >= (anomalies['date'].max() - pd.Timedelta(days=7))]
        if not recent_anomalies.empty:
            insights.append(f"📅 {len(recent_anomalies)} anomalies in the last 7 days need attention")
        
        return insights