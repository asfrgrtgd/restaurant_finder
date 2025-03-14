from flask import Flask, render_template, jsonify, request
import os
import googlemaps
import math

app = Flask(__name__)

# 環境変数から APIキーを取得（必要に応じて書き換え）
API_KEY = os.getenv('GOOGLE_API_KEY', 'YOUR_API_KEY_HERE')

# googlemaps クライアントの初期化
gmaps = googlemaps.Client(key=API_KEY)

def calculate_distance(lat1, lng1, lat2, lng2):
    """
    2点間の緯度経度から直線距離(m)を計算するヘルパー関数
    """
    radius = 6371000  # 地球の半径(m)
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = radius * c

    return distance

@app.route('/')
def index():
    """
    メインページの表示
    """
    return render_template('index.html')

@app.route('/search_restaurants', methods=['POST'])
def search_restaurants():
    """
    指定座標から一定半径内のレストランや関連施設を検索して返す。
    最終的に距離チェックし、radius 外のものは除外。
    """
    data = request.get_json()
    lat = float(data.get('lat', 35.607))
    lng = float(data.get('lng', 140.106))
    radius = int(data.get('radius', 1500))

    # 半径のバリデーション
    MIN_RADIUS = 1000  # 最小半径を1kmに設定
    MAX_RADIUS = 50000  # 上限を50kmに設定

    if radius < MIN_RADIUS:
        return jsonify({'error': f'検索半径は1km以上を指定してください（現在: {radius}m）'})
    if radius > MAX_RADIUS:
        return jsonify({'error': f'検索半径が大きすぎます。最大半径は{MAX_RADIUS}mです。'})

    try:
        app.logger.debug(f'検索パラメータ: lat={lat}, lng={lng}, radius={radius}')

        # 検索対象に含める place_type のリスト
        place_types = [
            'restaurant', 'cafe', 'bakery', 'bar', 'meal_takeaway',
            'food', 'ice_cream', 'night_club', 'meal_delivery',
            'liquor_store'
        ]

        all_results = []
        seen_places = set()

        # 複数の place_type を順次検索
        for place_type in place_types:
            try:
                app.logger.debug(f'{place_type}の検索を開始')
                result = gmaps.places_nearby(
                    location=(lat, lng),
                    radius=radius,
                    type=place_type,
                    open_now=False
                )

                # status が OK の場合のみ results を処理
                if result.get('status') == 'OK':
                    for place in result.get('results', []):
                        place_id = place.get('place_id')
                        # 重複除外
                        if place_id and place_id not in seen_places:
                            all_results.append(place)
                            seen_places.add(place_id)

                app.logger.debug(f'{place_type}の検索完了: {len(result.get("results", []))}件')
            except Exception as e:
                app.logger.error(f'{place_type}の検索中にエラーが発生: {str(e)}')
                # 一部でエラーが起きても他のtypeは処理継続
                continue

        # 最終的に結果が空の場合
        if not all_results:
            app.logger.warning('検索結果が0件でした')
            return jsonify({'restaurants': []})

        # API 全体としてのステータスは基本 OK を想定
        # ZERO_RESULTS は普通に結果0件として扱う

        processed_results = []
        for place in all_results:
            # geometry情報があれば距離計算
            if 'geometry' in place and 'location' in place['geometry']:
                place_lat = place['geometry']['location']['lat']
                place_lng = place['geometry']['location']['lng']
                distance = calculate_distance(lat, lng, place_lat, place_lng)

                # ここで最終的に radius 内のものだけに絞る
                if distance <= radius:
                    # rating が無い場合は 0.0 とする
                    rating_value = place.get('rating', 0.0)
                    if not isinstance(rating_value, (int, float)):
                        try:
                            rating_value = float(rating_value)
                        except:
                            rating_value = 0.0

                    processed_results.append({
                        'name': place.get('name', '名称不明'),
                        'vicinity': place.get('vicinity', '住所不明'),
                        'rating': rating_value,
                        'distance': f"{distance:.1f}",  # 小数1桁表示
                        'photo_reference': place.get('photos', [{}])[0].get('photo_reference', None),
                        'place_id': place.get('place_id'),
                        'location': {
                            'lat': place_lat,
                            'lng': place_lng
                        }
                    })

        # ソート（距離の昇順）
        sorted_results = sorted(processed_results, key=lambda x: float(x['distance']))

        return jsonify({'restaurants': sorted_results})

    except Exception as e:
        app.logger.error(f'予期せぬエラー: {str(e)}')
        return jsonify({'error': str(e)})

@app.route('/get_current_location', methods=['GET'])
def get_current_location():
    """
    IP や Wifi 情報などを元に推定した位置情報を取得（正確性は環境依存）。
    """
    try:
        result = gmaps.geolocate()  # Google Maps Geolocation API 呼び出し
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    # 開発用サーバ起動
    app.run(debug=True)
