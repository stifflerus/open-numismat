import json
import urllib.request

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication

from OpenNumismat.private_keys import MAPS_API_KEY
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Settings import Settings

importedQtWebKit = True
try:
    from PyQt5.QtWebKitWidgets import QWebView
except ImportError:
    print('PyQt5.QtWebKitWidgets module missed. Google Maps not available')
    importedQtWebKit = False

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no"/>
    <style type="text/css">
        html {
            height: 100%;
        }
        body {
            height: 100%;
            margin: 0;
            padding: 0
        }
        #map {
            height: 100%
        }
    </style>
    <script>
var map;
var marker = null;

function initialize() {
  var position = {lat: 0, lng: 0};
  map = new google.maps.Map(
  document.getElementById('map'), {
    zoom: 4,
    center: position,
    streetViewControl: false,
    fullscreenControl: false
  });

  google.maps.event.addListener(map, 'dragend', function () {
    var center = map.getCenter();
    qtWidget.mapMoved(center.lat(), center.lng());
  });
  google.maps.event.addListener(map, 'click', function (ev) {
    if (marker === null) {
      lat = ev.latLng.lat();
      lng = ev.latLng.lng();
      gmap_addMarker(lat, lng);
      qtWidget.markerMoved(lat, lng)
    }
  });
}
function gmap_addMarker(lat, lng) {
  var position = {lat: lat, lng: lng};
  marker = new google.maps.Marker({
    position: position,
    map: map,
    draggable: true
  });

  google.maps.event.addListener(marker, 'dragend', function () {
    qtWidget.markerMoved(marker.position.lat(), marker.position.lng());
  });
  google.maps.event.addListener(marker, 'rightclick', function () {
    gmap_deleteMarker();
    qtWidget.markerRemoved();
  });
}
function gmap_deleteMarker() {
  marker.setMap(null);
  delete marker;
  marker = null;
}
function gmap_moveMarker(lat, lng) {
  var coords = new google.maps.LatLng(lat, lng);
  if (marker === null) {
    gmap_addMarker(lat, lng);
  }
  else {
    marker.setPosition(coords);
  }
  map.setCenter(coords);
}
    </script>
    <script async defer
            src="https://maps.googleapis.com/maps/api/js?key=API_KEY&callback=initialize&language=LANGUAGE"
            type="text/javascript"></script>
</head>
<body>
<div id="map"></div>
</body>
</html>
'''


class GMapsWidget(QWebView):
    mapMoved = pyqtSignal(float, float)
    mapClicked = pyqtSignal(float, float)
    mapRightClicked = pyqtSignal(float, float)
    mapDoubleClicked = pyqtSignal(float, float)

    markerMoved = pyqtSignal(float, float)
    markerRemoved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.language = Settings()['locale']

        self.initialized = False
        self.loadFinished.connect(self.onLoadFinished)
        self.page().mainFrame().addToJavaScriptWindowObject(
            "qtWidget", self)
        html = HTML.replace("API_KEY", MAPS_API_KEY).replace("LANGUAGE", self.language)
        self.setHtml(html)
        self.mapMoved.connect(self.mapIsMoved)

    def onLoadFinished(self):
        self.initialized = True

    @waitCursorDecorator
    def reverseGeocode(self, lat, lng):
        url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%f,%f&key=%s&language=%s" % (lat, lng, MAPS_API_KEY, self.language)

        try:
            req = urllib.request.Request(url)
            data = urllib.request.urlopen(req).read()
            json_data = json.loads(data.decode())
            return json_data['results'][0]['formatted_address']
        except:
            return ''

    @waitCursorDecorator
    def waitUntilReady(self):
        while not self.initialized:
            QApplication.processEvents()

    def moveMarker(self, lat, lng):
        self.runScript("gmap_moveMarker(%f, %f)" % (lat, lng))

    def mapIsMoved(self, lat, lng):
        print('mapIsMoved', lat, lng)

    def runScript(self, script):
        return self.page().mainFrame().evaluateJavaScript(script)