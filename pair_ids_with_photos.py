
import pathlib
import sqlite3
import sys


def main():
    with sqlite3.connect('data.sqlite') as c:
        for photo in pathlib.Path('photos').iterdir():
            if not c.execute('SELECT * FROM data WHERE id=?', (photo.stem,))\
                    .fetchone():
                print('No person found for ' + repr(photo), file=sys.stderr)
            c.execute('UPDATE data SET image=? where id=?',
                      ('https://cdn.rawgit.com/wfdd/nc-assembly-scraper'
                       '/master/photos/' + photo.name, photo.stem))

if __name__ == '__main__':
    main()
