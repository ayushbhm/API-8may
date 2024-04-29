from flask import request, jsonify,Blueprint,render_template
from models.models import db, Genre, Movie, MovieGenre, Person, Roles, MoviePersonRole
from sqlalchemy.orm import joinedload
import requests
manage_movies_bp = Blueprint('manage_movies', __name__)

@manage_movies_bp.route('/manage_movies')
def manage_movies():
    response = requests.get('http://127.0.0.1:5000/api/update_movie_details')
    if response.status_code == 200:
        movie_details = response.json()
    roles=get_all_roles()
    genres =get_all_genres()
    persons = get_all_persons()
    
    MoviePersonRole = get_all_moviepersonrole()
    return render_template('manage_movies.html',movie_details=movie_details, roles= roles, genres= genres, persons= persons,MoviePersonRole=MoviePersonRole)


@manage_movies_bp.route('/api/update_movie_details', methods=['GET'])
def update_movie_details():
    try:
        # Query all movies
        movies = Movie.query.all()

        # Prepare a list to store all movie details
        movies_details = []

        for movie in movies:
            # Query associated genres for each movie
            genres = (
                db.session.query(Genre)
                .join(MovieGenre, Genre.name == MovieGenre.genre_name)
                .filter(MovieGenre.movie_id == movie.id)
                .all()
            )
            genre_names = [genre.name for genre in genres]

            # Query persons and their roles associated with the movie
            persons_with_roles = (
                db.session.query(Person, Roles, MoviePersonRole)
                .join(MoviePersonRole, Person.id == MoviePersonRole.person_id)
                .join(Roles, MoviePersonRole.role_name == Roles.name)
                .filter(MoviePersonRole.movie_id == movie.id)
                .all()
            )
            
            # Prepare details for the current movie
            movie_details = {
                'movie_id':movie.id,
                'movie_name': movie.name,
                'year': movie.year,
                'imdb_rating': movie.imdb_rating,
                'genres': genre_names,
                'persons': []
            }

            for person, role, movie_person_role in persons_with_roles:
                movie_details['persons'].append({
                    'person_name': person.personname,
                    'role_name': role.name,
                    'person_id': person.id
                    
                })

            
            movies_details.append(movie_details)

        return jsonify(movies_details), 200

    except Exception as e:
        return jsonify({'message': f'Failed to fetch movie details. Error: {str(e)}'}), 500


@manage_movies_bp.route('/update_movie_request', methods=['POST'])
def update_movie_request():
    try:
       
        movie_id = request.form['movie_id']
        new_name = request.form['name']
        new_year = request.form['year']
        new_imdb_rating = request.form['imdb_rating']
        genre_name = request.form['genre']
        person_ids = request.form.getlist('person_id[]')
        roles = request.form.getlist('role[]')
        
        
        
        movie = Movie.query.get(movie_id)
        
        if movie:
            movie.name = new_name
            movie.year = new_year
            movie.imdb_rating = new_imdb_rating
            db.session.commit()
        else:
            return jsonify({'error': 'Movie with ID {movie_id} not found'})

        
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


def get_all_genres():
    return [( genre.name) for genre in Genre.query.all()]

def get_all_persons():
    return [(person.id, person.personname) for person in Person.query.all()]

def get_all_roles():
    return [( role.name) for role in Roles.query.all()]


def get_all_moviepersonrole():
    
    query = db.session.query(
        MoviePersonRole.movie_id,
        MoviePersonRole.person_id,
        MoviePersonRole.role_name,
        Person.personname
    ).outerjoin(
        Person,
        MoviePersonRole.person_id == Person.id
    )

    
    movie_person_roles = query.all()

    return movie_person_roles
