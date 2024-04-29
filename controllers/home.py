from flask import request, jsonify,Blueprint
from models.models import db, Genre, Movie, MovieGenre, Person, Roles, MoviePersonRole

home_bp = Blueprint('home', __name__)



@home_bp.route('/api/movies', methods=['GET'])
def get_movies():
    movies = Movie.query.all()
    movies_data = [{'id': movie.id, 'name': movie.name, 'year': movie.year, 'imdb_rating': movie.imdb_rating} for movie in movies]
    return jsonify(movies_data)



@home_bp.route('/api/movie_details/<int:movie_id>', methods=['GET'])
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
        
        print(persons_with_roles)

        
        movie_details = {
            'movie_name': movie.name,
            'year': movie.year,
            'imdb_rating': movie.imdb_rating,
            'genres': genre_names,
            'persons': []
        }

        for person, role, movie_person_role in persons_with_roles:
            movie_details['persons'].append({
                'person_name': person.personname,
                'role_name': role.name
            })

        return jsonify(movie_details), 200

    except Exception as e:
        return jsonify({'message': f'Failed to fetch movie details. Error: {str(e)}'}), 500





@home_bp.route('/api/check_delete_actor/', methods=['POST'])
def check_delete_actor():
    person_id = request.form.get('person_id')
    person_id = int(person_id)
    
   
    if not person_id:
        return jsonify({'error':'ID required' })
    
    check_movie_assciativity= MoviePersonRole.query.filter_by(person_id=person_id,role_name="actor").first()
    
    
    print(check_movie_assciativity)
    
    if check_movie_assciativity:
        return "person associated with movie as an actor"
    else:
        delete_it =Person.query.filter_by(id=person_id).first()
        db.session.delete(delete_it)
        db.session.commit()
        return "Deleted Successfully"
        
    
    
    

