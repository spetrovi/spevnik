#!/usr/bin/python3
import json
import glob
import os
import subprocess
import optparse
import shutil
from jinja2 import Template

class Spevnik:
    def __init__(self, directories, output, book_name, mode):
        self.directories = directories
        self.output = output.rstrip('/')
        self.book_name = book_name
        self.mode = mode
        
        if self.mode == 'R':
            self.chapters = [self.generate_region(_dir) for _dir in self.directories]
        if self.mode == 'D':
            self.chapters = [self.generate_villages(_dir) for _dir in self.directories]
        
        book_template = Template(self.read_file('./templates/book.jinja2'))
        self.book = book_template.render(completed='\n'.join(self.chapters))
        
        
    def generate_region(self, region_path):
        name = region_path.rstrip('/').split('/')[-1]
        path_to_villages = glob.glob(region_path.rstrip('/') + '/*')
        village_sections = (self.generate_village(path) for path in path_to_villages)
        region_chapter = "\chapter*{" + name + "}\n" + '\n\n'.join(village_sections)
        return region_chapter
        
        
    def generate_village(self, village_path):
        name = village_path.rstrip('/').split('/')[-1]
        path_to_jsons = glob.glob(village_path + '/*.json')
        songs = []

        for path in path_to_jsons:
            with open(path, 'r') as f:
                try:
                    songs.append(json.load(f))
                except Exception as e:
                    print('Loading of file ' + path + ' failed')
                    print(e)

        if self.mode == 'R':
            village_section = "\section*{" + name + "}\n"
        elif self.mode == 'D':
            village_section = "\chapter*{" + name + "}\n"
        for song in songs:
            song_template = Template(self.read_file('./templates/song.jinja2'))
            slohy = []
            for i, sloha in enumerate(song['sloha']):
                sloha_template = Template(self.read_file('./templates/sloha.jinja2'))
                sloha = map(lambda verse: "\"" + verse + "\"", sloha)
                slohy.append(sloha_template.render(num=str(i+1), verses = '\n'.join(sloha)))
            if len(slohy) == 0:
                print('Error, empty song: ' + song['metadata']['nazov'])
            else:
                column_template = column_template = Template(self.read_file('./templates/columns/'+str(len(slohy))+'column.jinja2'))
                column_lilypond = column_template.render(sloha=slohy)
        
                song_lilypond = song_template.render(song=song, slohy=column_lilypond)
                village_section += song_lilypond + '\n'                
        return village_section
        
    def read_file(self, name):
        try:
            with open(name, 'r') as f:
                _string = f.read()
                return _string
        except Exception as e:
            print('Exception in reading file: ' + name)
            print(e)
               
    def save(self, book):
        try:
            os.makedirs(self.output)
        except Exception as e:
            print(e)
        lytex_path = self.output + '/' + book 
        with open(lytex_path, 'w') as f:
            f.write(self.book)
        return lytex_path
            
    def build(self):
        if os.path.exists(self.output):
            shutil.rmtree(self.output)
        lytex_path = self.save(self.book_name +'.lytex')
        
        proc = subprocess.Popen(['lilypond-book', '--output=' + self.output, '--pdf', lytex_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        outs, errs = proc.communicate()
        if errs:
            print('There were some errors running lilypond-book:')
#            print(errs)
            
        orig_dir = os.path.abspath('.')
        os.chdir(self.output)
        proc = subprocess.Popen(['pdflatex', '-interaction=nonstopmode', self.book_name + '.tex'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            out, errs = proc.communicate()
        except Exception as e:
            os.chdir(orig_dir)
        os.chdir(orig_dir)
        pdf_path = self.output + '/' + self.book_name + '.pdf'
        if os.path.exists(pdf_path):
            print('Success, generated songbook is: ' + pdf_path)
            if os.path.exists('texput.log'):
                os.remove('texput.log')
        else:
            print('Some occured with pdflatex, here is tex log: ')
            if os.path.exists('texput.log'):
                print(self.read_file('texput.log'))
                os.remove('texput.log')
            else:
                print('No texput.log')        

            
usage = ''' ./spevnik_generator.py [options]
Generate songbook from all songs
    $ ./spevnik_generator.py -a

Generate songbook from a single region
        $ ./complete_generator.py -r 'Stredné Považie'
        
Generate songbook from multiple regions
        $ ./complete_generator.py -r 'Stredné Považie':'Horná Nitra'

Generate songbook from a single village
        $ ./complete_generator.py -d 'Selec'

Generate songbook from multiple villages
        $ ./complete_generator.py -d 'Selec':'Stankovce'
                       
'''
        
        

parser = optparse.OptionParser(usage)
parser.add_option('-a', '--all', dest='parse_all', action='store_true', help='generate songbook from all songs present in this repo')
parser.add_option('-r', '--region', dest='region', type='string', help='generate songbook from this region or multiple regions separated by colon')
parser.add_option('-d', '--dedina', dest='dedina', type='string', help='generate songbook from this village or multiple villages separated by colon')
parser.add_option('-o', '--output_path', default='./build', dest='output_path', type='string', help='specify where to build the songbook')
parser.add_option('-n', '--name', default='spevnik', dest='book_name', type='string', help='specify name of the new book')
(options, args) = parser.parse_args()

if options.parse_all:
    spevnik_object = Spevnik(glob.glob('./Slovensko/*'), options.output_path, options.book_name, mode='R')
elif options.region:
    regiony = map(lambda x: './Slovensko/' + x, options.region.split(':'))
    spevnik_object = Spevnik(regiony, options.output_path, options.book_name, mode='R')
elif options.dedina:
    dediny = map(lambda dedina: './Slovensko/*/' + dedina ,options.dedina.split(':'))
    dediny = map(lambda dedina: glob.glob(dedina), dediny)
    spevnik_object = Spevnik(dediny, options.output_path, book_name, mode='D')
spevnik_object.build()
