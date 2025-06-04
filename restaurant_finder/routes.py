from flask import Blueprint, render_template, jsonify, request, current_app

from .utils import calculate_distance

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/search_restaurants', methods=['POST'])
def search_restaurants():
    data = request.get_json()
    lat = float(data.get('lat', 35.607))
    lng = float(data.get('lng', 140.106))
    radius = int(data.get('radius', 1500))

    MIN_RADIUS = 1000
    MAX_RADIUS = 50000

    if radius < MIN_RADIUS:
        return jsonify({'error': f'検索半径は1km以上を指定してください（現在: {radius}m）'})
    if radius > MAX_RADIUS:
        return jsonify({'error': f'検索半径が大きすぎます。最大半径は{MAX_RADIUS}mです。'})

    gmaps = current_app.config['GMAPS_CLIENT']

    try:
        current_app.logger.debug(f'検索パラメータ: lat={lat}, lng={lng}, radius={radius}')

        place_types = [
            'restaurant', 'cafe', 'bakery', 'bar', 'meal_takeaway',
            'food', 'ice_cream', 'night_club', 'meal_delivery',
            'liquor_store'
        ]

        all_results = []
        seen_places = set()

        for place_type in place_types:
            try:
                current_app.logger.debug(f'{place_type}の検索を開始')
                result = gmaps.places_nearby(
                    location=(lat, lng),
                    radius=radius,
                    type=place_type,
                    open_now=False
                )

                if result.get('status') == 'OK':
                    for place in result.get('results', []):
                        place_id = place.get('place_id')
                        if place_id and place_id not in seen_places:
                            all_results.append(place)
                            seen_places.add(place_id)

                current_app.logger.debug(f"{place_type}の検索完了: {len(result.get('results', []))}件")
            except Exception as e:
                current_app.logger.error(f'{place_type}の検索中にエラーが発生: {str(e)}')
                continue

        if not all_results:
            current_app.logger.warning('検索結果が0件でした')
            return jsonify({'restaurants': []})

        processed_results = []
        for place in all_results:
            if 'geometry' in place and 'location' in place['geometry']:
                place_lat = place['geometry']['location']['lat']
                place_lng = place['geometry']['location']['lng']
                distance = calculate_distance(lat, lng, place_lat, place_lng)

                if distance <= radius:
                    rating_value = place.get('rating', 0.0)
                    if not isinstance(rating_value, (int, float)):
                        try:
                            rating_value = float(rating_value)
                        except Exception:
                            rating_value = 0.0

                    processed_results.append({
                        'name': place.get('name', '名称不明'),
                        'vicinity': place.get('vicinity', '住所不明'),
                        'rating': rating_value,
                        'distance': f"{distance:.1f}",
                        'photo_reference': place.get('photos', [{}])[0].get('photo_reference', None),
                        'place_id': place.get('place_id'),
                        'location': {
                            'lat': place_lat,
                            'lng': place_lng
                        }
                    })

        sorted_results = sorted(processed_results, key=lambda x: float(x['distance']))
        return jsonify({'restaurants': sorted_results})

    except Exception as e:
        current_app.logger.error(f'予期せぬエラー: {str(e)}')
        return jsonify({'error': str(e)})


@bp.route('/get_current_location', methods=['GET'])
def get_current_location():
    try:
        gmaps = current_app.config['GMAPS_CLIENT']
        result = gmaps.geolocate()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

