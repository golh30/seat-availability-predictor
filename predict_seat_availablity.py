import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import numpy as np

# Get the database credentials from secrets
db_host = st.secrets.db["host"]
db_user = st.secrets.db["user"]
db_password = st.secrets.db["password"]
db_name = st.secrets.db["name"]

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password
    )

# Load trip data
def load_trip_data():
    conn = get_db_connection()
    query = """
    SELECT journey_date, departure_time, created_at, seats_available
    FROM seat_booked
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    df['journey_date'] = pd.to_datetime(df['journey_date'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

# Predict seat availability for remaining days until journey_date
def predict_seat_availability(df, journey_date, departure_time):
    today = datetime.today().date()
    
    # Filter data for the last 5 days before journey_date
    history_start = journey_date - timedelta(days=5)
    df = df[(df['journey_date'].between(
            pd.Timestamp(history_start, tz="UTC"), 
            pd.Timestamp(journey_date - timedelta(days=1), tz="UTC")
        )) & (df['departure_time'] == departure_time)].copy()
    
    if df.empty:
        return None

    # Convert timestamps to numerical values
    df['timestamp'] = df['created_at'].astype(int) / 10**9  # Convert to seconds since epoch

    # Train Linear Regression Model
    model = LinearRegression()
    X = df[['timestamp']].values  # Features (Time)
    y = df['seats_available'].replace('Full', 0).values  # Target (Seats Available)

    if len(df) > 1:
        model.fit(X, y)

        # Predict seat availability from today to journey_date
        future_dates = [today + timedelta(days=i) for i in range((journey_date - today).days + 1)]
        future_timestamps = np.array([datetime.combine(date, datetime.min.time()).timestamp() for date in future_dates]).reshape(-1, 1)
        future_seats = model.predict(future_timestamps)

        future_df = pd.DataFrame({
            'date': future_dates,
            'seats_available': np.maximum(future_seats, 0)  # Ensure no negative values
        })
        return future_df
    else:
        return None

# Main Streamlit App
def main():
    df = load_trip_data()

    st.sidebar.header("Filter Options")
    selected_date = st.sidebar.date_input("Select Journey Date", df['journey_date'].min())

    date_filtered_df = df[df['journey_date'].dt.date == selected_date]

    if date_filtered_df.empty:
        st.warning(f"No data found for {selected_date}")
        return

    unique_departure_times = sorted(date_filtered_df['departure_time'].unique())

    selected_departure = st.sidebar.selectbox("Select Departure Time", unique_departure_times)

    trip_df = date_filtered_df[date_filtered_df['departure_time'] == selected_departure]

    if trip_df.empty:
        st.warning("No data available for this departure time.")
        return

    # Show seat availability history
    st.subheader(f"Seat Availability Timeline - Departure {selected_departure}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trip_df['created_at'],
        y=trip_df['seats_available'],
        mode='lines+markers',
        name='Seats Available',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title="Seat Availability Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Seats Available",
        hovermode="x unified"
    )

    st.plotly_chart(fig)

    # Predict Future Seat Availability
    future_df = predict_seat_availability(df, selected_date, selected_departure)

    if future_df is not None:
        st.subheader("Predicted Seat Availability Until Journey Date")

        pred_fig = go.Figure()
        pred_fig.add_trace(go.Scatter(
            x=future_df['date'],
            y=future_df['seats_available'],
            mode='lines+markers',
            name='Predicted Seats Available',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ))

        pred_fig.update_layout(
            title="Predicted Seat Availability",
            xaxis_title="Date",
            yaxis_title="Seats Available",
            hovermode="x unified"
        )

        st.plotly_chart(pred_fig)
        st.dataframe(future_df)
    else:
        st.warning("Not enough data to predict seats.")

if __name__ == "__main__":
    main()