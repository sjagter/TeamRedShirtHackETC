from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
    test_var = "test_var"
    return render_template('app.html', test_var=test_var)

# Example of other route
@app.route('/hello')
def hello():
    return 'Hello, World'