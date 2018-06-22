# Pyglet imports
import pyglet

from pyglet.gl import *
from pyglet.window import key as KEY
from pyglet import clock

# Other imports
import random
import math

clamp = lambda num, min_num, max_num: min(max(num, min_num), max_num)

class Blocks:
    """
    Stores all the block ids and their properties
    """
    properties = {
        0: {
            "texture": "brick.png",
            "solid": True
        },
        1: {
            "texture": "glass.png",
            "solid": False
        }
    }
    brick = 0
    glass = 1

class Position:
    """
    A class for 3D positions
    """

    def __init__(self, x, y, z):

        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)

    def tuple(self):
        return (self.x, self.y, self.z)


class Rotation:
    """
    A class for rotations
    """

    def __init__(self, x, y):

        self.x = x
        self.y = y

class Textures:
    """
    Stores and loads textures
    """

    # Create library
    library = {}

    def get(self, block):
        """
        Gets a texture
        """

        # Check if texture exists in library
        if Textures.library.get(block) == None:
            # Load texture
            file = Blocks.properties[block]["texture"]
            texture = pyglet.image.load(file).texture
            
            # Set filtering to nearest, so that pixel art isn't blurry
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

            # Put TextureGroup of the texture into the texture library
            Textures.library[block] = pyglet.graphics.TextureGroup(texture)

        # Return texture
        return Textures.library.get(block)

class Chunk:
    """
    Stores and renders the blocks
    """

    chunks = []

    def is_inbounds(self, position):
        """
        Check if the position given is in the chunk
        """

        # Split position into 3 variables
        x, y, z = position.tuple()
        
        # Return if x, y, and z are greater than or equal 0 and less than or equal to 15
        return (
            (x >= 0 and x <= 15)
            and 
            (y >= 0 and y <= 15)
            and 
            (z >= 0 and z <= 15)
        )

    def is_solid(self, position):
        """
        Check if giving position is solid
        """

        # If the position is inbound, return the property "solid" of that block
        if self.is_inbounds(position):
            return Blocks.properties[self.get_block(position)]["solid"]

        # Otherwise, return false
        else:
            return False

    def get_block(self, position):
        """
        Returns the block id at a given position
        """
        
        # Convert position into tuple and check that tuple again block dict
        return self.blocks[position.tuple()]

    def __init__(self, chunk_x, chunk_y, chunk_z):
        """
        Create the chunk
        """
        
        # Generate chunk
        self.batch = pyglet.graphics.Batch()
        self.blocks = {}

        # Create 16x16 cube of random glass or brick
        for x in range(16):
            for y in range(16):
                for z in range(16):
                    self.blocks[(x, y, z)] = random.randint(0, 1)

        # Generate the batch
        self.generate_batch()

        # Add chunk to chunk list
        Chunk.chunks.append(self)

    def generate_batch(self):
        """
        Creates the batch to be draw
        """

        # Texture coordinates for the faces
        texture_coordinates = ("t2f", (0,0, 1,0, 1,1, 0,1))

        # Go through the blocks
        for block_position in self.blocks:
            # Turn block position into the position class
            block_position = Position(*block_position)
            
            # Get block type and texture
            block_type = self.get_block(block_position)
            block_tex = Window.textures.get(block_type)
            
            # Bottom corner
            x, y, z = block_position.tuple()

            # Top opposite corner
            X, Y, Z = x + 1, y + 1, z + 1

            # If the block on the top is not solid, add it to the chunk's batch
            if not self.is_solid(block_position + Position(0, 1, 0)):
                self.batch.add(4, GL_QUADS, block_tex, ('v3f', (x,Y,Z, X,Y,Z, X,Y,z, x,Y,z)), texture_coordinates)

            # If the block on the bottom is not solid, add it to the chunk's batch
            if not self.is_solid(block_position - Position(0, 1, 0)):
                self.batch.add(4, GL_QUADS, block_tex, ('v3f', (x,y,z, X,y,z, X,y,Z, x,y,Z)), texture_coordinates)

            # If the block on the left is not solid, add it to the chunk's batch
            if not self.is_solid(block_position - Position(1, 0, 0)):
                self.batch.add(4, GL_QUADS, block_tex, ('v3f', (x,y,z, x,y,Z, x,Y,Z, x,Y,z)), texture_coordinates)

            # If the block on the right is not solid, add it to the chunk's batch
            if not self.is_solid(block_position + Position(1, 0, 0)):
                self.batch.add(4, GL_QUADS, block_tex, ('v3f', (X,y,Z, X,y,z, X,Y,z, X,Y,Z)), texture_coordinates)

            # If the block on the front is not solid, add it to the chunk's batch
            if not self.is_solid(block_position + Position(0, 0, 1)):
                self.batch.add(4, GL_QUADS, block_tex, ('v3f', (x,y,Z, X,y,Z, X,Y,Z, x,Y,Z)), texture_coordinates)

            # If the block on the back is not solid, add it to the chunk's batch
            if not self.is_solid(block_position - Position(0, 0, 1)):
                self.batch.add(4, GL_QUADS, block_tex, ('v3f', (X,y,z, x,y,z, x,Y,z, X,Y,z)), texture_coordinates)

    def draw(self):
        self.batch.draw()

class Player:
    """
    Holds position and rotation of the player
    """
    def __init__(self):
        """
        Create player
        """
        
        # Create position and rotation
        self.pos = Position(0, 0, 0)
        self.rot = Rotation(0, 0)

    def mouse_motion(self, dx, dy):
        """
        Handles mouse motion for the player
        """
        
        # Divide mouse movement by 8
        dx /= 8
        dy /= 8

        # Rotate player based on mouse movement
        self.rot.x += dy
        self.rot.y -= dx

        # Clamp rotation to 90 degrees
        self.rot.x = clamp(self.rot.x, -90, 90)

    def update(self, delta, keys):
        """
        Updates player based on keypresses
        """

        # Calculate speed from delta
        speed = delta*10
        
        # Get rotation
        rot_y = (-self.rot.y / 180) * math.pi

        # Calculate move based on rotation
        move_x, move_z = speed*math.sin(rot_y), speed*math.cos(rot_y)

        # Move forward on W
        if keys[KEY.W]:
            self.pos.x += move_x
            self.pos.z -= move_z

        # Move backward on S
        if keys[KEY.S]:
            self.pos.x -= move_x
            self.pos.z += move_z

        # Move left on A
        if keys[KEY.A]:
            self.pos.x -= move_z
            self.pos.z -= move_x

        # Move right on D
        if keys[KEY.D]:
            self.pos.x += move_z
            self.pos.z += move_x

        # Move upwards on space
        if keys[KEY.SPACE]: 
            self.pos.y += speed
        
        # Move downwards on leftcontrol
        if keys[KEY.LCTRL]: 
            self.pos.y -= speed

class Window(pyglet.window.Window):
    """
    Main window for rendering the game
    """

    # Create texture library
    textures = Textures()

    # Init mouse lock to false
    lock = False

    def set_mode(self, mode):
        """
        Set rendering mode
        """
        
        # Set current matrix to projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        if mode == "3D":
            # Sets rendering mode to perspective (3D)
            gluPerspective(90, self.width/self.height, 0.05, 1000)        
        
        if mode == "2D":
            # Sets rendering mode to orthographic (2D)
            gluOrtho2D(0, self.width, 0, self.height)

        # Set current matrix to modelview
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def __init__(self, *args, **kwargs):
        """
        Creates the window
        """

        # Initialize pyglet.window.Window with it's self as window
        super().__init__(*args, **kwargs)

        # Set minimum size to 300, 200
        self.set_minimum_size(300, 200)

        # Push keypresses to self.keys
        self.keys = KEY.KeyStateHandler()
        self.push_handlers(self.keys)

        # Create fps display
        self.fps_display = clock.ClockDisplay()

        # Create player
        self.player = Player()

        # Create test chunk
        self.chunk = Chunk(0, 0, 0)

    def on_mouse_motion(self, x, y, dx, dy):
        """
        Handles mouse motion
        """
        
        # If the mouse is locked, push the mouse motion to the player
        if Window.lock:
            self.player.mouse_motion(dx, dy)

    def on_key_press(self, key, mod):
        """
        Handles keypresses
        """
        
        # If escape is pressed, close the window
        if key == KEY.ESCAPE:
            self.close()

        # If the E key is pressed, lock or unlock the mouse
        if key == KEY.E:
            Window.lock = not Window.lock
            self.set_exclusive_mouse(Window.lock)

    def on_draw(self):
        """
        Renders the game state
        """

        # Clear window
        self.clear()

        # Set render mode to 3D
        self.set_mode("3D")

        # Create a new frame to render
        glPushMatrix()

        # Rotate scene based on player rotation
        glRotatef(-self.player.rot.x, 1, 0, 0)
        glRotatef(-self.player.rot.y, 0, 1, 0)

        # Move scene based on player position
        glTranslatef(-self.player.pos.x, -self.player.pos.y, -self.player.pos.z)

        # Draw chunk
        self.chunk.draw()

        # Set render mode to 2D
        self.set_mode("2D")

        # Draw fps counter
        self.fps_display.draw()

        # Move the next frame to render to be rendered
        glPopMatrix()

    def update(self, dt):
        """
        Updates the game state
        """

        # Update the player
        self.player.update(dt, self.keys)

if __name__ == "__main__":
    # Create window and schedule update function
    window = Window(400, 300, "Block", resizable=True)
    pyglet.clock.schedule(window.update)
    
    # Set background color to a light blue
    glClearColor(0.5, 0.6, 1, 1)
    
    # Makes it so that farther stuff renders first
    glEnable(GL_DEPTH_TEST)

    # Removes back of faces
    glEnable(GL_CULL_FACE)

    # Allows transparent textures
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Run pyglet.
    pyglet.app.run()