#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
# from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import *
from flask_migrate import Migrate
from datetime import datetime
import pytz
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
# moment = Moment(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

# app_context = app.app_context()
# app_context.push()
# db.init_app(app)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

utc=pytz.UTC
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    all_area = db.session.query(Venue.state, Venue.city).group_by(Venue.state, Venue.city).all()

    for area in all_area:
        sub_data = []
        venues = Venue.query.filter_by(state=area.state, city=area.city).all()
        for venue in venues:
            sub_data.append({
                'id': venue.id, 
                'name': venue.name
            })
        data.append({
            'state': area.state,
            'city': area.city, 
            'venues': sub_data
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    response = {}
    search_word = request.form['search_term']
    city = request.form.get('city')
    state = request.form.get('state')

    if city:    
        venues = Venue.query.filter(Venue.name.ilike(f'%{search_word}%'), Venue.city == city).all()
    if state:
        venues = Venue.query.filter(Venue.name.ilike(f'%{search_word}%'), Venue.state == state).all()
    if city and state:
        venues = Venue.query.filter(Venue.name.ilike(f'%{search_word}%'), Venue.city == city, Venue.state == state).all()
    if not city and not state:
        venues = Venue.query.filter(Venue.name.ilike(f'%{search_word}%')).all()

    response['count'] = len(venues)
    lst = []

    for venue in venues:
        lst.append({
            'id': venue.id, 
            'name': venue.name
        })

    response['data'] = lst
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    data = {
        "id": venue_id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link, 
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0
    }

    for show in venue.shows:
        show_time = show.start_time.replace(tzinfo=utc)
        current_time = datetime.now().replace(tzinfo=utc)
        if show_time < current_time:
            data['past_shows'].append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
            })
            data['past_shows_count'] += 1
        else:
            data['upcoming_shows'].append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
            })
            data['upcoming_shows_count'] += 1        
    
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']
        image_link = request.form['image_link']
        website_link = request.form['website_link']
        seeking_talent = True if 'seeking_talent' in request.form else False
        seeking_description = request.form['seeking_description']

        new_venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link, seeking_talent=seeking_talent, seeking_description=seeking_description)

        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash(f'Venue {venue.name} was successfully deleted.')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash(f'An error occurred. Venue {venue.name} could not be deleted.')
    finally:
        db.session.close()
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    # response = {
    #     "count": 1,
    #     "data": [{
    #         "id": 4,
    #         "name": "Guns N Petals",
    #         "num_upcoming_shows": 0,
    #     }]
    # }

    response = {}
    search_word = request.form['search_term']
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_word}%')).all()

    response['count'] = len(artists)
    lst = []

    for artist in artists:
        lst.append({
            'id': artist.id, 
            'name': artist.name
        })

    response['data'] = lst
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)
    data = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link, 
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0
    }

    for show in artist.shows:
        show_time = show.start_time.replace(tzinfo=utc)
        current_time = datetime.now().replace(tzinfo=utc)
        if show_time < current_time:
            data['past_shows'].append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
            })
            data['past_shows_count'] += 1
        else:
            data['upcoming_shows'].append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
            })
            data['upcoming_shows_count'] += 1  
    
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    
    form.name.data = artist.name
    form.state.data = artist.state
    form.city.data = artist.city
    form.phone.data = artist.phone
    form.website_link.data = artist.website_link
    form.seeking_description.data = artist.seeking_description
    form.seeking_venue.data = artist.seeking_venue
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.get(artist_id)
    try:
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')
        artist.facebook_link = request.form['facebook_link']
        artist.image_link = request.form['image_link']
        artist.website_link = request.form['website_link']
        artist.seeking_venue = True if 'seeking_venue' in request.form else False
        artist.seeking_description = request.form['seeking_description']
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash(f'An error occurred. Artist {artist.name} could not be updated.')
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    
    form.name.data = venue.name
    form.state.data = venue.state
    form.city.data = venue.city
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.website_link.data = venue.website_link
    form.seeking_description.data = venue.seeking_description
    form.seeking_talent.data = venue.seeking_talent
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)

    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.genres = request.form.getlist('genres')
        venue.facebook_link = request.form['facebook_link']
        venue.image_link = request.form['image_link']
        venue.website_link = request.form['website_link']
        venue.seeking_talent = True if 'seeking_talent' in request.form else False
        venue.seeking_description = request.form['seeking_description']
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash(f'An error occurred. Venue {venue.name} could not be updated.')
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        print('state', type(state))
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        print('genres', type(genres))
        facebook_link = request.form['facebook_link']
        image_link = request.form['image_link']
        website_link = request.form['website_link']
        seeking_venue = True if 'seeking_venue' in request.form else False
        seeking_description = request.form['seeking_description']

        new_artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website_link=website_link, seeking_venue=seeking_venue, seeking_description=seeking_description)

        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows = Show.query.all()
    data=[]
    for show in shows:
        data.append({
            'artist_image_link': show.artist.image_link, 
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S'), 
            'artist_id': show.artist_id, 
            'artist_name': show.artist.name,
            'venue_id': show.venue_id, 
            'venue_name': show.venue.name
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    date_time = datetime.strptime(request.form['start_time'], '%Y-%m-%d %H:%M:%S').date()
    artist = request.form['artist_id']
    shows = Artist.query.get(artist).shows
    repeated = False

    for show in shows:
        if date_time == show.start_time.date():
            repeated = True

    if not repeated:
        try:
            artist_id = request.form['artist_id']
            venue_id = request.form['venue_id']
            start_time = request.form['start_time']

            show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
            db.session.add(show)
            db.session.commit()
            flash('Show was successfully listed!')
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()
    else:
        flash('Artist is busy in this day !!')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(port=3000, debug=False)

# Or specify p§ort manually:

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='127.0.0.1', port=port)



# <Config {'ENV': 'production',
# 'DEBUG': True,
# 'TESTING': False,
# 'PROPAGATE_EXCEPTIONS': None,
# 'PRESERVE_CONTEXT_ON_EXCEPTION': None,
# 'SECRET_KEY': b'\x80\x98\xd3\xb1\xabDK\xb0\xea\xabR\x81\xa1\x18!\x1bf\xb5\xfb\xdfe\x80WF\xcb\xe3\xc8[\xb3d,\xe3',
# 'PERMANENT_SESSION_LIFETIME': datetime.timedelta(days=31),
# 'USE_X_SENDFILE': False,
# 'SERVER_NAME': None,
# 'APPLICATION_ROOT': '/',
# 'SESSION_COOKIE_NAME': 'session',
# 'SESSION_COOKIE_DOMAIN': None,
# 'SESSION_COOKIE_PATH': None,
# 'SESSION_COOKIE_HTTPONLY': True,
# 'SESSION_COOKIE_SECURE': False,
# 'SESSION_COOKIE_SAMESITE': None,
# 'SESSION_REFRESH_EACH_REQUEST': True,
# 'MAX_CONTENT_LENGTH': None,
# 'SEND_FILE_MAX_AGE_DEFAULT': datetime.timedelta(seconds=43200),
# 'TRAP_BAD_REQUEST_ERRORS': None,
# 'TRAP_HTTP_EXCEPTIONS': False,
# 'EXPLAIN_TEMPLATE_LOADING': False,
# 'PREFERRED_URL_SCHEME': 'http',
# 'JSON_AS_ASCII': True,
# 'JSON_SORT_KEYS': True,
# 'JSONIFY_PRETTYPRINT_REGULAR': False,
# 'JSONIFY_MIMETYPE': 'application/json',
# 'TEMPLATES_AUTO_RELOAD': None,
# 'MAX_COOKIE_SIZE': 4093,
# 'SQLALCHEMY_DATABASE_URI': '<Put your local database url>',
# 'SQLALCHEMY_TRACK_MODIFICATIONS': False,
# 'SQLALCHEMY_BINDS': None,
# 'SQLALCHEMY_NATIVE_UNICODE': None,
# 'SQLALCHEMY_ECHO': False,
# 'SQLALCHEMY_RECORD_QUERIES': None,
# 'SQLALCHEMY_POOL_SIZE': None,
# 'SQLALCHEMY_POOL_TIMEOUT': None,
# 'SQLALCHEMY_POOL_RECYCLE': None,
# 'SQLALCHEMY_MAX_OVERFLOW': None,
# 'SQLALCHEMY_COMMIT_ON_TEARDOWN': False,
# 'SQLALCHEMY_ENGINE_OPTIONS': {}}>
