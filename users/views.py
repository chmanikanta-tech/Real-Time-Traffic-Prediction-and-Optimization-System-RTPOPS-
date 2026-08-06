from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import pandas as pd
import os

from .models import UserRegistrationModel

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserRegistrationModel  # Adjust if model is imported differently

def UserRegisterActions(request):
    if request.method == 'POST':
        # Create a new user object from form data
        user = UserRegistrationModel(
            name=request.POST['name'],
            loginid=request.POST['loginid'],
            password=request.POST['password'],
            mobile=request.POST.get('mobile', ''),
            email=request.POST['email'],
            locality=request.POST.get('locality', ''),
            address=request.POST.get('address', ''),
            status='waiting'
        )
        user.save()
        messages.success(request, "Registration successful! Please wait for admin approval.")
        return redirect('UserLogin')
    
    # If GET request, show the registration form
    return render(request, 'userRegistration.html')



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserRegistrationModel

def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('password')

        try:
            check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            if check.status == "active":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = loginid
                request.session['email'] = check.email
                return redirect('UserHome')
            else:
                messages.warning(request, 'Your account is not yet activated. Please wait for admin approval.')
                return redirect('UserLogin')
        except UserRegistrationModel.DoesNotExist:
            messages.error(request, 'Invalid login ID or password.')
            return redirect('UserLogin')

    return render(request, 'login.html')



def UserHome(request):
    if not request.session.get('id'):
        return redirect('UserLogin')
    return render(request, 'users/UserHome.html')


def base(request):
    return render(request, 'base.html')


def index(request):
    return render(request, "index.html")


def logout_view(request):
    request.session.flush()
    return redirect('index')

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from django.shortcuts import render
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
import joblib

def training(request):
    csv_path = 'media/Traffic.csv'
    if not os.path.exists(csv_path):
        return render(request, 'users/training.html', {
            'error': f"Dataset not found at {csv_path}"
        })

    try:
        df = pd.read_csv(csv_path, usecols=['Day of the week', 'Time', 'Total'])

        # Day feature
        day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                   'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        df['day_value'] = df['Day of the week'].map(day_map).astype(np.int8)
        df['sin_day'] = np.sin(2 * np.pi * df['day_value'] / 7)
        df['cos_day'] = np.cos(2 * np.pi * df['day_value'] / 7)
        df['is_weekend'] = df['day_value'].isin([5, 6]).astype(np.int8)

        # Time features
        df['Time'] = pd.to_datetime(df['Time'], format='%I:%M:%S %p')
        df['hour'] = df['Time'].dt.hour
        time_sec = df['Time'].dt.hour * 3600 + df['Time'].dt.minute * 60 + df['Time'].dt.second
        df['time_sin'] = np.sin(2 * np.pi * time_sec / 86400)
        df['time_cos'] = np.cos(2 * np.pi * time_sec / 86400)

        # Lag features
        df['prev_total'] = df['Total'].shift(1)
        df['rolling_mean_3'] = df['Total'].rolling(window=3).mean()
        df['rolling_std_3'] = df['Total'].rolling(window=3).std()
        df.dropna(inplace=True)

        # Features and labels
        features = ['sin_day', 'cos_day', 'time_sin', 'time_cos', 'hour',
                    'is_weekend', 'prev_total', 'rolling_mean_3', 'rolling_std_3']
        X = df[features]
        y = df['Total'].astype(np.float32)

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split data
        train_X, test_X, train_y, test_y = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, shuffle=True
        )

        # Model
        model = XGBRegressor(
            n_estimators=600,
            learning_rate=0.03,
            max_depth=8,
            min_child_weight=2,
            subsample=0.9,
            colsample_bytree=0.9,
            gamma=0.1,
            reg_lambda=0.8,
            reg_alpha=0.3,
            early_stopping_rounds=25,
            eval_metric='rmse',
            n_jobs=-1
        )
        model.fit(train_X, train_y, eval_set=[(test_X, test_y)], verbose=False)

        # Predictions
        pred = model.predict(test_X)
        rmse = np.sqrt(mean_squared_error(test_y, pred))
        r2 = r2_score(test_y, pred)
        accuracy = np.mean(np.abs(pred - test_y) <= 0.10 * test_y) * 100

        # Save model and scaler
        model_path = 'static/model/xgboost_traffic_model.pkl'
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump({'model': model, 'scaler': scaler}, model_path)

        # Save prediction plot
        plot_path = 'static/plots/pred_vs_actual.png'
        os.makedirs(os.path.dirname(plot_path), exist_ok=True)
        plt.figure(figsize=(10, 6))
        plt.scatter(test_y, pred, c='green', alpha=0.6)
        plt.plot([test_y.min(), test_y.max()], [test_y.min(), test_y.max()], 'r--')
        plt.xlabel("Actual Total")
        plt.ylabel("Predicted Total")
        plt.title(f"RMSE: {rmse:.2f}, R²: {r2:.2f}, Accuracy: {accuracy:.2f}%")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()

        return render(request, 'users/training.html', {
            'rmse': f"{rmse:.2f}",
            'r2': f"{r2:.2f}",
            'accuracy': f"{accuracy:.2f}",
            'plot_url': f'/{plot_path}',
            'model_path': model_path
        })

    except Exception as e:
        return render(request, 'users/training.html', {
            'error': f"An error occurred during training: {str(e)}"
        })
    
# import os
# import numpy as np
# import pandas as pd
# import joblib
# from datetime import datetime
# from django.shortcuts import render

# def projection(request):
#     if request.method == 'POST':
#         try:
#             # Form inputs
#             time_str = request.POST.get('time')  # Format: 08:30 AM or 13:30
#             day_str = request.POST.get('day')
#             car = int(request.POST.get('carcount'))
#             bike = int(request.POST.get('bikecount'))
#             bus = int(request.POST.get('buscount'))
#             truck = int(request.POST.get('truckcount'))

#             # Total and lag features
#             total = car + bike + bus + truck
#             prev_total = total
#             rolling_mean_3 = total
#             rolling_std_3 = 0  # No history in manual entry

#             # Day features
#             day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
#                        'Friday': 4, 'Saturday': 5, 'Sunday': 6}
#             day_val = day_map.get(day_str)
#             if day_val is None:
#                 raise ValueError("Invalid day selected.")
#             sin_day = np.sin(2 * np.pi * day_val / 7)
#             cos_day = np.cos(2 * np.pi * day_val / 7)
#             is_weekend = 1 if day_val in [5, 6] else 0

#             # Time features (supports both 12h and 24h format)
#             try:
#                 dt = datetime.strptime(time_str, "%I:%M %p")  # 12-hour
#             except ValueError:
#                 dt = datetime.strptime(time_str, "%H:%M")     # 24-hour

#             hour = dt.hour
#             seconds = dt.hour * 3600 + dt.minute * 60 + dt.second
#             time_sin = np.sin(2 * np.pi * seconds / 86400)
#             time_cos = np.cos(2 * np.pi * seconds / 86400)

#             # Load model
#             model_path = 'static/model/xgboost_traffic_model.pkl'
#             if not os.path.exists(model_path):
#                 return render(request, 'users/projection.html', {'error': "Model file not found."})

#             loaded = joblib.load(model_path)
#             model = loaded['model']
#             scaler = loaded['scaler']

#             # Prepare input
#             input_df = pd.DataFrame([{
#                 'sin_day': sin_day,
#                 'cos_day': cos_day,
#                 'time_sin': time_sin,
#                 'time_cos': time_cos,
#                 'hour': hour,
#                 'is_weekend': is_weekend,
#                 'prev_total': prev_total,
#                 'rolling_mean_3': rolling_mean_3,
#                 'rolling_std_3': rolling_std_3
#             }])

#             scaled_input = scaler.transform(input_df)
#             predicted_total = model.predict(scaled_input)[0]

#             return render(request, 'users/projection.html', {
#                 'prediction': f"{predicted_total:.2f}",
#                 'inputs': {
#                     'Time': time_str,
#                     'Day': day_str,
#                     'CarCount': car,
#                     'BikeCount': bike,
#                     'BusCount': bus,
#                     'TruckCount': truck,
#                     'Computed Total': total
#                 }
#             })

#         except Exception as e:
#             return render(request, 'users/projection.html', {'error': f"Prediction failed: {str(e)}"})

#     return render(request, 'users/projection.html')

import os
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from django.shortcuts import render

# Load dataset once for displaying a single output field
dataset_path = r'C:\Users\PRAKASH\Downloads\Traffic projection using M.L\traffic_projection\media\Traffic.csv'
if os.path.exists(dataset_path):
    traffic_df = pd.read_csv(dataset_path)
    output_fields = traffic_df['Traffic Situation'].unique().tolist()
    single_output = output_fields[0] if output_fields else None
else:
    single_output = None

def projection(request):
    if request.method == 'POST':
        try:
            # Form inputs
            time_str = request.POST.get('time')  # Format: 08:30 AM or 13:30
            day_str = request.POST.get('day')
            car = int(request.POST.get('carcount'))
            bike = int(request.POST.get('bikecount'))
            bus = int(request.POST.get('buscount'))
            truck = int(request.POST.get('truckcount'))
            total = int(request.POST.get('Total'))

            # Total and lag features
            total = car + bike + bus + truck
            prev_total = total
            rolling_mean_3 = total
            rolling_std_3 = 0  # No history in manual entry

            # Day features
            day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                       'Friday': 4, 'Saturday': 5, 'Sunday': 6}
            day_val = day_map.get(day_str)
            if day_val is None:
                raise ValueError("Invalid day selected.")
            sin_day = np.sin(2 * np.pi * day_val / 7)
            cos_day = np.cos(2 * np.pi * day_val / 7)
            is_weekend = 1 if day_val in [5, 6] else 0

            # Time features
            try:
                dt = datetime.strptime(time_str, "%I:%M %p")  # 12-hour format
            except ValueError:
                dt = datetime.strptime(time_str, "%H:%M")     # 24-hour format

            hour = dt.hour
            seconds = dt.hour * 3600 + dt.minute * 60 + dt.second
            time_sin = np.sin(2 * np.pi * seconds / 86400)
            time_cos = np.cos(2 * np.pi * seconds / 86400)

            # Load model
            model_path = 'static/model/xgboost_traffic_model.pkl'
            if not os.path.exists(model_path):
                return render(request, 'users/projection.html', {
                    'error': "Model file not found.",
                    'output_field': single_output
                })

            loaded = joblib.load(model_path)
            model = loaded['model']
            scaler = loaded['scaler']

            # Prepare input for prediction
            input_df = pd.DataFrame([{
                'sin_day': sin_day,
                'cos_day': cos_day,
                'time_sin': time_sin,
                'time_cos': time_cos,
                'hour': hour,
                'is_weekend': is_weekend,
                'prev_total': prev_total,
                'rolling_mean_3': rolling_mean_3,
                'rolling_std_3': rolling_std_3

            }])

            scaled_input = scaler.transform(input_df)
            predicted_total = model.predict(scaled_input)[0]

            return render(request, 'users/projection.html', {
                'prediction': f"{predicted_total:.2f}",
                'inputs': {
                    'Time': time_str,
                    'Day': day_str,
                    'CarCount': car,
                    'BikeCount': bike,
                    'BusCount': bus,
                    'TruckCount': truck,
                    'Computed Total': total
                },
                'output_field': single_output
            })

        except Exception as e:
            return render(request, 'users/projection.html', {
                'error': f"Prediction failed: {str(e)}",
                'output_field': single_output
            })

    # For GET request just render page with output_field
    return render(request, 'users/projection.html', {'output_field': single_output})


