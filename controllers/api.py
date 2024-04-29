from flask import request, jsonify,Blueprint,render_template,url_for
from models.models import db, Genre, Movie, MovieGenre, Person, Roles, MoviePersonRole
import requests
api_bp = Blueprint('home', __name__)


#POST API to Delete an actor who is not associated with any Movie.
@api_bp.route('/api/check_delete_actor/', methods=['POST'])
def check_delete_actor():
    person_id = request.form.get('person_id')
    person_id = int(person_id)
    
   
    if not person_id:
        return jsonify({'error':'ID required' }),400
    
    check_movie_assciativity= MoviePersonRole.query.filter_by(person_id=person_id,role_name="actor").first()
    

    
    if check_movie_assciativity:
        return jsonify({'message': 'Person associated with movie as an actor'}), 200
    else:
        delete_it =Person.query.filter_by(id=person_id).first()
        db.session.delete(delete_it)
        db.session.commit()
        return jsonify({'message': 'Deleted Successfully'}), 200
    

#GET API to fetch all the details of a particular movie like genres, persons associated, year etc. 
@api_bp.route('/api/movie_details/<int:movie_id>', methods=['GET'])
def get_movie_details(movie_id):
    try:
        
        movie = Movie.query.get(movie_id)

        if not movie:
            return jsonify({'message': 'Movie not found.'}), 404

        
        genres = (
            db.session.query(Genre)
            .join(MovieGenre, Genre.name == MovieGenre.genre_name)
            .filter(MovieGenre.movie_id == movie_id)
            .all()
        )
        genre_names = [genre.name for genre in genres]

        
        persons_with_roles = (
            db.session.query(Person, Roles, MoviePersonRole)
            .join(MoviePersonRole, Person.id == MoviePersonRole.person_id)
            .join(Roles, MoviePersonRole.role_name == Roles.name)
            .filter(MoviePersonRole.movie_id == movie_id)
            .all()
        )
        
        #print(persons_with_roles)

        
        movie_details = {
            'movie_name': movie.name,
            'year': movie.year,
            'imdb_rating': movie.imdb_rating,
            'genres': genre_names,
            'persons': []
        }

        for person, role in persons_with_roles:
            movie_details['persons'].append({
                'person_name': person.personname,
                'role_name': role.name
            })

        return jsonify(movie_details), 200

    except Exception as e:
        return jsonify({'message': f'Failed to fetch movie details. Error: {str(e)}'}), 500



#POST API to update the details of movie, 
@api_bp.route('/update_movie_request', methods=['POST'])
def update_movie_request():
    try:
       
        movie_id = request.form['movie_id']
        new_name = request.form['name']
        new_year = request.form['year']
        new_imdb_rating = request.form['imdb_rating']
        genre_name = request.form['genre']
        person_ids = request.form.getlist('person_id[]')
        roles = request.form.getlist('role[]')
        #We are fetching all the old details along with the new details 
        
        
        movie = Movie.query.get(movie_id)
        
        if movie:
            movie.name = new_name
            movie.year = new_year
            movie.imdb_rating = new_imdb_rating
            db.session.commit()
        else:
            return jsonify({'error': 'Movie with ID {movie_id} not found'}),404

        
        movie_genre = MovieGenre.query.filter_by(movie_id=movie_id).first()
        movie_genre.genre_name = genre_name
    
        
        for person_id,role in zip(person_ids,roles):
            
            column_to_be_updated = MoviePersonRole.query.filter_by(movie_id=movie_id, person_id=person_id).first()
            print(column_to_be_updated)
            if column_to_be_updated:
                column_to_be_updated.role_name = role
                db.session.commit()

        db.session.commit()
        return jsonify({'message': 'Movie updated successfully!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return "some error occured"



#Fetch all the paginated movie data using helper Api 
@api_bp.route('/')
def index():
    response = requests.get('http://127.0.0.1:5000/api/movies')
    performers_response = requests.get('http://127.0.0.1:5000/api/performers')
    #APIConfig could have been used here instead.
    
    
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
        


#Helper API 1 of the previous 
@api_bp.route('/api/movies', methods=['GET'])
def get_movies():
    movies = Movie.query.all()
    movies_data = [{'id': movie.id, 'name': movie.name, 'year': movie.year, 'imdb_rating': movie.imdb_rating} for movie in movies]
    return jsonify(movies_data)

#Helper function 2 to fetch actors and directors
@api_bp.route('/api/performers', methods=['GET'])
def get_performers():
    try:
        
        performers_roles = (
            db.session.query(Person.personname, Roles.name)
            .join(MoviePersonRole, Person.id == MoviePersonRole.person_id)
            .join(Roles, Roles.name == MoviePersonRole.role_name)
            .filter(Roles.name.in_(['actor', 'director'])) 
            .distinct() 
            .all()
        )
        
        
        
        actors = [performer[0] for performer in performers_roles if performer[1] == 'actor']
        directors = [performer[0] for performer in performers_roles if performer[1] == 'director']

        
        return jsonify({'actors': actors, 'directors': directors}), 200

    except Exception as e:
        
        return jsonify({'message': f'Failed to fetch performers. Error: {str(e)}'}), 500


#API to get paginated filtered movies i.e seach through combination of actor and directors
@api_bp.route('/search', methods=['GET'])
def search():
    performers_url = 'http://127.0.0.1:5000/api/performers'
    performers_response = requests.get(performers_url)

    actors = []
    directors = []
    if performers_response.status_code == 200:
        performers_data = performers_response.json()
        actors = performers_data.get('actors', [])
        directors = performers_data.get('directors', [])
    
    actor_name = request.args.get('actor')
    director_name = request.args.get('director')

    filtered_movies_url = f'http://127.0.0.1:5000/api/filtered_movies'
    params = {'actor': actor_name, 'director': director_name}
    response = requests.get(filtered_movies_url, params=params)

    
    movies = []
    if response.status_code == 200:
        movies_data = response.json().get('movies', [])
        
        page = request.args.get('page', default=1, type=int)
        per_page = 2 

        
        movies = paginate_items(movies_data, page, per_page)

        
        prev_page = url_for('search.search', actor=actor_name, director=director_name, page=page - 1) if page > 1 else None
        next_page = url_for('search.search', actor=actor_name, director=director_name, page=page + 1) if len(movies) == per_page else None

    
    return render_template('search_results.html', movies=movies, actors=actors, directors=directors, prev=prev_page, next=next_page)


def paginate_items(items, page, per_page):
    total_items = len(items)
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    paginated_items = items[start_idx:end_idx]
    return paginated_items


#POST API to add a new movie
@api_bp.route('/add_movie_request', methods=['POST'])
def add_movie_request():
    try:
        
        name = request.form['name']
        year = request.form['year']
        imdb_rating = request.form['imdb_rating']
        genre_name = request.form['genre']
        person_ids = request.form.getlist('person_id[]')
        roles = request.form.getlist('role[]')
        
        
        new_movie = Movie(name=name, year=year, imdb_rating=imdb_rating)
        db.session.add(new_movie)
        db.session.commit()
        
        
        new_movie_genre = MovieGenre(movie_id=new_movie.id, genre_name=genre_name)
        db.session.add(new_movie_genre)
        
        
        for person_id, role in zip(person_ids, roles):
            new_person_role = MoviePersonRole(movie_id=new_movie.id, person_id=person_id, role_name=role)
            db.session.add(new_person_role)
        
        db.session.commit()
        
        return jsonify({'message': 'Movie added successfully!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add movie'})