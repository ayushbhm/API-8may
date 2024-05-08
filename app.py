from flask import Flask,render_template,request
from models.models import db
app = Flask(__name__)
import requests
from controllers.home import home_bp;
app.register_blueprint(home_bp)
from controllers.api import api_bp;
app.register_blueprint(api_bp)

from controllers.search import search_bp;
app.register_blueprint(search_bp)
from controllers.manage_movies import manage_movies_bp;
app.register_blueprint(manage_movies_bp)



app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///10Ex.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)



@app.route('/')
def index():
    response = requests.get('http://127.0.0.1:5000/api/movies')
    performers_response = requests.get('http://127.0.0.1:5000/api/performers')

    actors = []
    directors = []

    if performers_response.status_code == 200:
        performers_data = performers_response.json()
        actors = performers_data.get('actors', [])
        directors = performers_data.get('directors', [])

    all_movies = []
    if response.status_code == 200:
        all_movies = response.json()

    
    page = request.args.get('page', default=1, type=int)
    per_page = 2 

    
    total_items = len(all_movies)
    total_pages = (total_items + per_page - 1) // per_page  

   
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    paginated_movies = all_movies[start_idx:end_idx]

    
    prev_page = f"/?page={page - 1}" if page > 1 else None
    next_page = f"/?page={page + 1}" if page < total_pages else None

    return render_template('mainpage.html', all_movies=paginated_movies,
                           actors=actors, directors=directors,
                           prev=prev_page, next=next_page)



@app.route('/movie_details/<int:movie_id>')
def movie_details_page(movie_id):
    api_url = f'http://127.0.0.1:5000/api/movie_details/{movie_id}'
    response = requests.get(api_url)
    if response.status_code == 200:
            
        movie_details = response.json()
    else:
            
        movie_details = {}

    return render_template('movie_details.html',movie_details=movie_details)





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
