from flask import Flask, render_template, request, redirect, url_for, send_file
from pymongo import MongoClient
import requests
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/myDatabase'
client = MongoClient(app.config['MONGO_URI'])
db = client.Userinfo
data_collection = db.users
weather_collection = db.weather_collect

@app.route('/')
def index():
    return render_template('registration.html')

@app.route('/registration', methods=['POST', 'GET'])
def registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if data_collection.find_one({'email': email}):
            return render_template('registration.html', error='Email already exists')
        else:
            data_collection.insert_one({'name': name, 'email': email, 'password': password})
            return render_template('login.html')
    else:
        return render_template('registration.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print("Email received in login route:", email)  # Add this print statement

        user = data_collection.find_one({'email': email, 'password': password})

        if user:
            return redirect(url_for('weather', email=email))
        else:
            return render_template('login.html', error='Invalid email or password')
    else:
        return render_template('login.html')

@app.route('/weather')
def weather():
    email = request.args.get('email')
    city_name = request.args.get('city')  
    
    print("Email received in weather route:", email)  # Add this print statement
    
    weatherApiKey = '398cf001831322c70c89176e8e04e7b3'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={weatherApiKey}'
    
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        temperature = weather_data['main']['temp']
        description = weather_data['weather'][0]['description'].capitalize()
        humidity = weather_data['main']['humidity']
        wind_speed = weather_data['wind']['speed']
        db.weather_collect.insert_one({'search_history': {'email': email, 'city': city_name, 'weather_data': weather_data}})
        
        
        return render_template('weather.html', email=email, temperature=temperature, description=description, humidity=humidity, wind_speed=wind_speed)
    else:
        return render_template('weather.html', error='Failed to retrieve weather data')

@app.route('/logout', methods=['POST'])
def logout():
    return redirect(url_for('index'))

@app.route('/export_to_excel', methods=['POST'])
def export_to_excel():
    email = request.form.get('email')
    
    # Retrieve weather data for the logged-in user from MongoDB
    user_weather_data = weather_collection.find({'search_history.email': email})
    
    # Convert retrieved data into a DataFrame
    data = []
    for item in user_weather_data:
        data.append(item['search_history'])
    df = pd.DataFrame(data)
    
    # Export DataFrame to Excel
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    
    # Send the Excel file as a response
    return send_file(excel_file, as_attachment=True, download_name='weather_data.xlsx')

if __name__ == '__main__':
    app.run(debug=True)
