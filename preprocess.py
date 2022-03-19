import json
from jinja2 import Template
import glob
def read_file(name):
    f = open(name, 'r')
    string = f.read()
    f.close()
    return string
#class Report:
#    def __init__(self, source, baseline, target, destination, storage_string):
#        self.success = False
#        self.info = Info(source, baseline, target, destination, storage_string)
#        self.set_benchmark_specific_vars()
        
#template = Template(read_file('./html_templates/header.jinja2'))
#header = template.render(info=self.info, config=CONFIG)        

region = "Stredné Považie"
dedina = "Selec"

paths = glob.glob('regióny/' + '/'.join([region,dedina]) + '/*.json')

songs = []

for path in paths:
    with open(path) as f:
        songs.append(json.load(f))

generated = ""
for song in songs:
    song_template = Template(read_file('./templates/song.jinja2'))
    slohy = []
    for i, sloha in enumerate(song['sloha']):
        sloha_template = Template(read_file('./templates/sloha.jinja2'))
        sloha = map(lambda verse: "\"" + verse + "\"", sloha)
        slohy.append(sloha_template.render(num=str(i+1), verses = '\n'.join(sloha)))

    if len(slohy) == 4:
        column_template = Template(read_file('./templates/columns/4slohy.jinja2'))
    elif len(slohy) == 3:
        column_template = Template(read_file('./templates/columns/3slohy.jinja2'))
    elif len(slohy) == 2:
        column_template = Template(read_file('./templates/columns/2slohy.jinja2'))
    elif len(slohy) == 1:
        column_template = Template(read_file('./templates/columns/1sloha.jinja2'))
    column_lilypond = column_template.render(sloha=slohy)

    song_lilypond = song_template.render(song=song, slohy=column_lilypond)
    generated += song_lilypond + '\n'

book_template = Template(read_file('./templates/book.jinja2'))
book_render = book_template.render(completed=generated)

f = open('out/book.lytex', 'w')
f.write(book_render)
f.close()
#template = Template(read_file('./html_templates/header.jinja2'))
#header = template.render(info=self.info, config=CONFIG)        

