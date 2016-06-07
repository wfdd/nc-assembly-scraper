
from collections import OrderedDict
import csv
import pathlib
import sqlite3
import sys


def main():
    with open('photos.csv', 'w') as f, \
            sqlite3.connect('data.sqlite') as c:
        csv_writer = csv.writer(f)
        ids_to_photo = OrderedDict(
            c.execute('SELECT DISTINCT(id), "" from data').fetchall())
        for photo in pathlib.Path('photos').iterdir():
            if photo.stem in ids_to_photo:
                ids_to_photo[photo.stem] = \
                    'https://cdn.rawgit.com/wfdd/nc-assembly-scraper/master/photos/' + \
                    photo.name
            else:
                print('No `id` found for ' + repr(photo), file=sys.stderr)
        csv_writer.writerow(('id', 'photo'))
        csv_writer.writerows(ids_to_photo.items())

if __name__ == '__main__':
    main()
