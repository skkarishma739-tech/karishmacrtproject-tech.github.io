from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)
# Temporary storage for users in a Python dictionary 
# Format -> 'username': 'password'
users = {}
@app.route('/')
def index():
    # Redirect root URL to login page
    return redirect(url_for('login'))
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if username already exists
        if username in users:
            return render_template('signup.html', error="Username already exists!")
            
        # Store user in dictionary
        users[username] = password
        
        # Registration successful, pass success message to template
        return render_template('signup.html', success="Registration Successful")
        
    # Render signup page for GET request
    return render_template('signup.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate credentials
        if username in users and users[username] == password:
            # Login successful, redirect to home with success message
            return redirect(url_for('home', message="Login Successful", username=username))
        else:
            # Login failed
            return render_template('login.html', error="Invalid Username or Password")
            
    # Render login page for GET request
    return render_template('login.html')
@app.route('/home')
def home():
    # Get parameters from URL (query string)
    message = request.args.get('message')
    username = request.args.get('username')
    
    # If accessed directly without logging in, redirect to login
    if not username:
        return redirect(url_for('login'))
        
    return render_template('home.html', message=message, username=username)
if __name__ == '__main__':
    app.run(debug=True)
