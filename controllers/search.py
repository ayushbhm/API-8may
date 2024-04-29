from flask import request, jsonify,Blueprint,render_template,request,url_for
from sqlalchemy.orm import aliased
from models.models import db, Genre, Movie, MovieGenre, Person, Roles, MoviePersonRole
import requests

search_bp = Blueprint('search', __name__)


@search_bp.route('/search', methods=['GET'])
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



@search_bp.route('/api/filtered_movies', methods=['GET'])
def get_filtered_movies():
    
    actor_name = request.args.get('actor')
    director_name = request.args.get('director')

    
    query = db.session.query(Movie)

    
    if actor_name and director_name:
        
        query = (
            query
            .filter(Movie.id.in_(
                db.session.query(Movie.id)
                .join(MoviePersonRole, Movie.id == MoviePersonRole.movie_id)
                .join(Person, Person.id == MoviePersonRole.person_id)
                .join(Roles, Roles.name == MoviePersonRole.role_name)
                .filter(Person.personname == actor_name)
                .filter(Roles.name == 'actor')
                .filter(Movie.id.in_(
                    db.session.query(Movie.id)
                    .join(MoviePersonRole, Movie.id == MoviePersonRole.movie_id)
                    .join(Person, Person.id == MoviePersonRole.person_id)
                    .join(Roles, Roles.name == MoviePersonRole.role_name)
                    .filter(Person.personname == director_name)
                    .filter(Roles.name == 'director')
                ))
            ))
        )
    elif actor_name:
        
        query = (
            query
            .filter(Movie.id.in_(
                db.session.query(Movie.id)
                .join(MoviePersonRole, Movie.id == MoviePersonRole.movie_id)
                .join(Person, Person.id == MoviePersonRole.person_id)
                .join(Roles, Roles.name == MoviePersonRole.role_name)
                .filter(Person.personname == actor_name)
                .filter(Roles.name == 'actor')
            ))
        )
    elif director_name:
        
        query = (
            query
            .filter(Movie.id.in_(
                db.session.query(Movie.id)
                .join(MoviePersonRole, Movie.id == MoviePersonRole.movie_id)
                .join(Person, Person.id == MoviePersonRole.person_id)
                .join(Roles, Roles.name == MoviePersonRole.role_name)
                .filter(Person.personname == director_name)
                .filter(Roles.name == 'director')
            ))
        )

    
    movies = query.all()

    
    movie_details = []
    for movie in movies:
        movie_details.append({
            'id': movie.id,
            'name': movie.name,
            'year': movie.year,
            'imdb_rating': movie.imdb_rating,
            'director': get_director_name(movie.id),
            'actors': [actor.personname for actor in get_actors(movie.id)]
        })

    
    return jsonify({'movies': movie_details})






def get_director_name(movie_id):
    director = (
        db.session.query(Person.personname)
        .join(MoviePersonRole, (Person.id == MoviePersonRole.person_id) & (MoviePersonRole.movie_id == movie_id))
        .filter(MoviePersonRole.role_name == 'director')
        .first()
    )
    return director.personname if director else None

def get_actors(movie_id):
    actors = (
        db.session.query(Person)
        .join(MoviePersonRole, (Person.id == MoviePersonRole.person_id) & (MoviePersonRole.movie_id == movie_id))
        .filter(MoviePersonRole.role_name == 'actor')
        .all()
    )
    return actors


@search_bp.route('/api/performers', methods=['GET'])
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

