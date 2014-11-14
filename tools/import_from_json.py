#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import json
import os
import sys

from PyQt5.QtCore import QStandardPaths
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication, QFileDialog
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type

sys.path.append('..')
from OpenNumismat.Collection.Collection import Collection
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase

app = QApplication(sys.argv)

HOME_PATH = ''
__docDirs = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
if __docDirs:
    HOME_PATH = os.path.join(__docDirs[0], "OpenNumismat")

json_file_name, _selectedFilter = QFileDialog.getOpenFileName(None,
                "Open collection", HOME_PATH,
                "Collections (*.json)")
if json_file_name:
    file_name = json_file_name.replace('.json', '.db')
    json_file = codecs.open(json_file_name, "r", "utf-8")
    data = json.load(json_file)

    collection = Collection(None)
    collection.create(file_name)

    image_path = file_name.replace('.db', '_images')

    desc = collection.getDescription()
    desc.author = data['description']['author']
    desc.title = data['description']['title']
    desc.description = data['description']['description']
    desc.save()

    model = collection.model()
    for coin_data in data['coins']:
        coin = model.record()
        for field, value in coin_data.items():
            if field in ('obverseimg', 'reverseimg', 'edgeimg',
                         'photo1', 'photo2', 'photo3', 'photo4'):
                img_file_name = os.path.join(image_path, value)
                image = QImage(img_file_name)
                coin.setValue(field, image)
            else:
                coin.setValue(field, value)

        model.insertRecord(-1, coin)

    print("Saving...")
    model.submitAll()

    print("Processed %d coins" % model.rowCount())
