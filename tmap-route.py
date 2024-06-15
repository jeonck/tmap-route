# https://skopenapi.readme.io/reference/poi-%EA%B2%80%EC%83%89-%EC%83%98%ED%94%8C%EC%98%88%EC%A0%9C
# https://skopenapi.readme.io/reference/%EA%B2%BD%EB%A1%9C%EC%95%88%EB%82%B4-%EC%83%98%ED%94%8C%EC%98%88%EC%A0%9C
import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json
import streamlit.components.v1 as components

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 TMAP API 키 읽기
app_key = os.getenv("TMAP_API_KEY")

# Streamlit 앱 설정
st.set_page_config(layout="wide")

def get_poi_by_keyword(keyword):
    """
    poi: points of interest
    """
    url = f'https://apis.openapi.sk.com/tmap/pois?version=1&appKey={app_key}&searchKeyword={keyword}'
    response = requests.get(url)
    result = response.json()
    first_poi = result['searchPoiInfo']['pois']['poi'][0]
    latitude = first_poi['noorLat']
    longitude = first_poi['noorLon']
    name = first_poi['name']
    poi = {
        'latitude': latitude,
        'longitude': longitude,
        'name': name
    }
    return poi

def get_total_time(start_poi, end_poi):
    url = f'https://apis.openapi.sk.com/tmap/routes?version=1&appKey={app_key}'
    data = {
        'startX': start_poi['longitude'],
        'startY': start_poi['latitude'],
        'endX': end_poi['longitude'],
        'endY': end_poi['latitude']
    }
    response = requests.post(url, json=data)
    result = response.json()
    total_time = result['features'][0]['properties']['totalTime']
    return total_time

# 출발지와 도착지 정보 입력받기
st.sidebar.header("출발지와 도착지 정보")
dep_keyword = st.sidebar.text_input("출발지 POI 키워드", "출발지 키워드 입력")
dest_keyword = st.sidebar.text_input("도착지 POI 키워드", "도착지 키워드 입력")

if st.sidebar.button("경로 안내"):
    # 출발지와 도착지 POI 검색
    dep_poi = get_poi_by_keyword(dep_keyword)
    dest_poi = get_poi_by_keyword(dest_keyword)

    dep_lon = dep_poi['longitude']
    dep_lat = dep_poi['latitude']
    dest_lon = dest_poi['longitude']
    dest_lat = dest_poi['latitude']

    # 걸리는 시간 계산
    total_time = get_total_time(dep_poi, dest_poi)

    # 경로 안내 API 호출
    api_url = f"https://apis.openapi.sk.com/tmap/routes/prediction?version=1&resCoordType=WGS84GEO&reqCoordType=WGS84GEO&sort=index&appKey={app_key}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "routesInfo": {
            "departure": {
                "name": "출발지",
                "lon": dep_lon,
                "lat": dep_lat,
                "depSearchFlag": "05"
            },
            "destination": {
                "name": "도착지",
                "lon": dest_lon,
                "lat": dest_lat,
                "destSearchFlag": "03"
            },
            "predictionType": "departure",
            "predictionTime": "2023-06-15T18:31:22+0900",
            "searchOption": "00",
            "tollgateCarType": "car",
            "trafficInfo": "N"
        }
    }

    response = requests.post(api_url, headers=headers, json=payload)
    route_data = response.json()

    # 지도 초기화 및 경로 및 POI 표시를 위한 HTML/JS 코드
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://apis.openapi.sk.com/tmap/jsv2?version=1&appKey={app_key}"></script>
        <style>
            #map_div {{
                width: 100%;
                height: 600px;
            }}
        </style>
    </head>
    <body>
        <div id="map_div"></div>
        <script>
            var map = new Tmapv2.Map("map_div", {{
                center: new Tmapv2.LatLng({dep_lat}, {dep_lon}),
                width: "100%",
                height: "600px",
                zoom: 10
            }});

            var routeData = {json.dumps(route_data)};

            if (routeData.features) {{
                routeData.features.forEach(function(feature) {{
                    if (feature.geometry.type === "LineString") {{
                        var linePath = feature.geometry.coordinates.map(function(coord) {{
                            return new Tmapv2.LatLng(coord[1], coord[0]);
                        }});
                        var polyline = new Tmapv2.Polyline({{
                            path: linePath,
                            strokeColor: "#FF0000",
                            strokeWeight: 6,
                            strokeOpacity: 0.7,
                            map: map
                        }});
                    }}
                }});
            }}

            var dep_poi = {json.dumps(dep_poi)};
            var dest_poi = {json.dumps(dest_poi)};

            var dep_marker = new Tmapv2.Marker({{
                position: new Tmapv2.LatLng(dep_poi.latitude, dep_poi.longitude),
                map: map,
                title: dep_poi.name
            }});

            var dep_infoWindow = new Tmapv2.InfoWindow({{
                position: new Tmapv2.LatLng(dep_poi.latitude, dep_poi.longitude),
                content: `<div>${dep_poi['name']}</div>`,
                map: map
            }});

            dep_marker.addListener("click", function() {{
                dep_infoWindow.open(map, dep_marker);
            }});

            var dest_marker = new Tmapv2.Marker({{
                position: new Tmapv2.LatLng(dest_poi.latitude, dest_poi.longitude),
                map: map,
                title: dest_poi.name
            }});

            var dest_infoWindow = new Tmapv2.InfoWindow({{
                position: new Tmapv2.LatLng(dest_poi.latitude, dest_poi.longitude),
                content: `<div>${dest_poi['name']}</div>`,
                map: map
            }});

            dest_marker.addListener("click", function() {{
                dest_infoWindow.open(map, dest_marker);
            }});
        </script>
    </body>
    </html>
    """

    # HTML/JS 코드 삽입
    components.html(map_html, height=600)

    # 총 소요 시간 표시
    st.write(f"출발지: {dep_poi['name']}")
    st.write(f"도착지: {dest_poi['name']}")
    st.write(f"걸리는 시간: {total_time // 60}분")
