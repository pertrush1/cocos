# This code is so you can run the samples without installing the package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import copy
import random


import pyglet
from pyglet.window import key
from pyglet.gl import *

from cocos.layer import *
from cocos.scene import Scene
from cocos.actions import *
from cocos.sprite import *
from cocos.euclid import *
from cocos.director import director

from constants import *
from status import status
import soundex
from HUD import *

__all__ = ['get_newgame']

class Colors( object ):
    colors = ['black','orange','red','yellow','cyan','magenta','green','blue',
            'black',        # don't remove
            'flip_x','flip_y','plus_one','minus_one',
            'black' ]       # don't remove

    BLACK,ORANGE,RED,YELLOW,CYAN,MAGENTA,GREEN,BLUE, LAST_COLOR, FLIP_X,FLIP_Y,PLUS_1, MINUS_1, LAST_SPECIAL = range( len(colors) )

    images = [ pyglet.resource.image('block_%s.png' % color) for color in colors ]
    
    specials = [ k for k in range( LAST_COLOR+1, LAST_SPECIAL) ]


class Game( Layer ):

    is_event_handler = True #: enable pyglet's events

    def __init__(self):
        super(Game,self).__init__()

        self.init_map()

        self.random_block()

        self.schedule( self.step )
        self.elapsed = 0
        self.used_key = False

        width, height = director.get_window_size()

        self.position = ( width/2 - COLUMNS * SQUARE_SIZE / 2, 0 )
        self.transform_anchor = (0,height/2)

        status.score = 0

    def on_enter(self):
        super(Game,self).on_enter()
        soundex.set_music('tetris.mp3')
        soundex.play_music()

    def on_exit(self):
        super(Game,self).on_exit()
        soundex.stop_music()

    def on_key_press(self, k, m ):
        if self.used_key:
            return

        if k in (key.LEFT, key.RIGHT, key.DOWN, key.UP):
            self.block.backup()

            if k == key.LEFT:
                self.block.pos.x -= 1
            elif k == key.RIGHT:
                self.block.pos.x += 1
            elif k == key.DOWN:
                self.block.pos.y -= 1
            elif k == key.UP:
                self.block.rotate()

            if not self.is_valid_block():
                self.block.restore()
                if k == key.DOWN:
                    self.next_block()

            self.used_key = True
            soundex.play("move.mp3")
            return True

        if k == key.SPACE:
            while True:
                # let the player move the block after it was dropped
                self.elapsed = 0

                self.block.backup()
                self.block.pos.y -= 1
                if not self.is_valid_block():
                    self.block.restore()
                    break
            soundex.play("drop.mp3")

    def on_text_motion(self, motion):
        if self.used_key:
            return
        if motion in (key.MOTION_DOWN, key.MOTION_RIGHT, key.MOTION_LEFT):
            self.block.backup()
            if motion == key.MOTION_DOWN:
                self.block.pos.y -= 1
            elif motion == key.MOTION_LEFT:
                self.block.pos.x -= 1
            elif motion == key.MOTION_RIGHT:
                self.block.pos.x += 1

            if not self.is_valid_block():
                self.block.restore()
                if motion == key.MOTION_DOWN:
                    self.next_block()

            self.used_key = True
            soundex.play("move.mp3")
            return True

    def init_map(self):
        '''creates a map'''
        self.map= {}
        for i in xrange( COLUMNS ):
            for j in xrange( ROWS ):
                self.map[ (i,j) ] = 0

    def draw( self ):
        '''draw the map and the block'''

        self.used_key = False
        glPushMatrix()
        self.transform()

        for i in xrange( COLUMNS ):
            for j in xrange( ROWS ):
                color = self.map.get( (i,j) )
                if color:
                    Colors.images[color].blit( i * SQUARE_SIZE, j* SQUARE_SIZE)
        self.block.draw()

        glPopMatrix()


    def step( self, dt ):
        '''updates the engine'''
        self.elapsed += dt
        if self.elapsed > 0.5:

#            if not self.are_valid_movements():
#                self.next_block()

            self.elapsed = 0
            self.block.pos.y -= 1
            if not self.is_valid_block():
                self.block.pos.y += 1
                self.next_block()


    def check_line(self):
        '''checks if the line is complete'''
        lines = []
        for j in xrange( ROWS ):
            for i in xrange( COLUMNS ):
                c = self.map.get( (i,j) )
                if not c:
                    break
                if i == COLUMNS-1:
                    lines.append(j)

        lines.reverse()

        if lines:
            soundex.play("line.mp3")
            status.score += pow(2, len(lines)) -1

        for l in lines:
            for j in xrange(l, ROWS-1 ):
                for i in xrange(COLUMNS):
                    self.map[ (i,j) ] = self.map[ (i,j+1) ]


    def merge_block( self ):
        '''merges a block in the map'''
        for i in xrange( self.block.x ):
            for j in xrange( self.block.x ):
                c= self.block.get(i,j)
                if c:
                    self.map[ (i+self.block.pos.x, j+self.block.pos.y) ] = c

    def are_valid_movements(self):
        '''check wheter there are any left valid movement'''
        for i in xrange(self.block.x):
            for j in xrange(self.block.x):
                if self.block.get(i,j):
                    if j + self.block.pos.y == 0:
                        return False
                    if self.map.get( (i + self.block.pos.x,j + self.block.pos.y -1), False ):
                        return False
        return True

    def next_block(self):
        self.merge_block()
        self.check_line()
        self.random_block()

    def random_block( self ):
        '''puts the next block in stage'''
        self.block = status.next_piece
        block = random.choice( (
            Block_L,
            Block_L2,
            Block_O,
            Block_I,
            Block_Z,
            Block_Z2,
            Block_A
            ) )
        status.next_piece = block()

        if not self.block:
            self.random_block()

    def is_valid_block( self ):
        '''check wheter the block is valid in the current position'''
        for i in xrange( self.block.x ):
            for j in xrange( self.block.x ):
                if self.block.get(i,j):
                    if self.block.pos.x+i < 0:
                        return False
                    if self.block.pos.x+i >= COLUMNS:
                        return False
                    if self.block.pos.y+j < 0:
                        return False
                    if self.map.get( (self.block.pos.x+i, self.block.pos.y+j), False ): 
                        return False
        return True


class Block( object ):
    def __init__(self):
        super( Block, self).__init__()

        self.pos = Point2( COLUMNS/2-1, ROWS )
        self.rot = 0

        for x in xrange( len(self._shape) ):
            for y in xrange( len( self._shape[x]) ):
                if self._shape[x][y]:
                    r = random.random()
                    if r < 0.1:
                        color = random.choice( Colors.specials )
                    else:
                        color = self.color
                    self._shape[x][y] = color

    def draw( self ):
        '''draw the block'''
        for i in xrange(self.x):
            for j in xrange(self.x):
                c = self.get(i,j)
                if c:
                    Colors.images[c].blit( (i + self.pos.x) * SQUARE_SIZE, (j + self.pos.y) * SQUARE_SIZE)

    def rotate( self ):
        '''rotate the block'''
        self.rot = (self.rot + 1) % self.mod

    def backup( self ):
        '''saves a copy of the block'''
        self.save_pos = copy.copy( self.pos )
        self.save_rot = self.rot

    def restore( self ):
        '''restore a copy of the block'''
        self.pos = self.save_pos
        self.rot = self.save_rot

    def get(self,x,y):
        '''get position x,y of the block'''
        if self.rot == 0:
            i,j = x,y
        elif self.rot == 1:
            i,j = y,(self.x -x -1 )
        elif self.rot == 2:
            i,j = (self.x - x -1), (self.x -y -1)
        elif self.rot == 3:
            i,j = (self.x - y -1 ), x

        return self._shape[i][j]


class Block_I( Block ):
    x = 4
    mod = 2
    color = Colors.RED

    def __init__(self):
        self._shape = [ [0,1,0,0],
                   [0,1,0,0],
                   [0,1,0,0],
                   [0,1,0,0] ]
        super(Block_I,self).__init__()

class Block_Z( Block ):
    x = 3
    color = Colors.ORANGE
    mod = 2

    def __init__(self):
        self._shape = [ [0,0,0],
                       [1,1,0],
                       [0,1,1] ]
        super(Block_Z,self).__init__()

class Block_Z2( Block ):
    x = 3
    color = Colors.CYAN
    mod = 2

    def __init__(self):
        self._shape = [ [0,0,0],
                       [0,1,1],
                       [1,1,0] ]
        super(Block_Z2,self).__init__()

class Block_O( Block ):
    x = 2
    color = Colors.BLUE
    mod = 4

    def __init__(self):
        self._shape = [ [1,1],
                       [1,1] ]
        super(Block_O,self).__init__()

class Block_L( Block ):
    x = 3
    color = Colors.MAGENTA
    mod = 4

    def __init__(self):
        self._shape = [ [1,0,0],
                       [1,0,0],
                       [1,1,0] ] 
        super(Block_L,self).__init__()

class Block_L2( Block ):
    x = 3
    color = Colors.YELLOW
    mod = 4

    def __init__(self):
        self._shape = [ [0,0,1],
                       [0,0,1],
                       [0,1,1] ] 
        super(Block_L2,self).__init__()

class Block_A( Block ):
    x = 3
    color = Colors.GREEN
    mod = 4

    def __init__(self):
        self._shape = [ [0,0,0],
                       [0,1,0],
                       [1,1,1] ] 
        super(Block_A,self).__init__()

def get_newgame():
    '''returns the game scene'''
    scene = Scene()
    scene.add( Game(), z=2 )
    scene.add( HUD(), z=1 )

    return scene